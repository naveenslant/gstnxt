from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from pathlib import Path

from app.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User, GSTProject, FileUpload, AnalysisResult
from app.services.file_validation_service import FileValidationService
from app.services.gst_analysis_service import GSTAnalysisService

router = APIRouter()

class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    month: str
    validation_status: str
    upload_status: str
    validation_errors: List[str] = []

@router.post("/upload/{project_id}", response_model=List[FileUploadResponse])
async def upload_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload GST files to project"""
    try:
        # Verify project ownership
        project = db.query(GSTProject).filter(
            GSTProject.id == project_id,
            GSTProject.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        upload_results = []
        
        for file in files:
            try:
                # Read file content
                content = await file.read()
                
                # Validate and process file
                result = await FileValidationService.validate_and_store_file(
                    db=db,
                    project_id=project_id,
                    filename=file.filename,
                    content=content,
                    gstin=project.gstin
                )
                
                upload_results.append(FileUploadResponse(
                    id=str(result["file_upload"].id),
                    filename=result["filename"],
                    file_type=result["file_type"],
                    month=result["month"],
                    validation_status=result["validation_status"],
                    upload_status=result["upload_status"],
                    validation_errors=result.get("validation_errors", [])
                ))
                
            except Exception as e:
                # Handle individual file errors
                upload_results.append(FileUploadResponse(
                    id="",
                    filename=file.filename,
                    file_type="unknown",
                    month="",
                    validation_status="failed",
                    upload_status="failed",
                    validation_errors=[str(e)]
                ))
        
        return upload_results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload files: {str(e)}"
        )

@router.get("/list/{project_id}")
async def list_uploaded_files(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List uploaded files for project"""
    try:
        # Verify project ownership
        project = db.query(GSTProject).filter(
            GSTProject.id == project_id,
            GSTProject.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        files = db.query(FileUpload).filter(
            FileUpload.project_id == project_id
        ).order_by(FileUpload.created_at.desc()).all()
        
        return {
            "files": [
                {
                    "id": str(file.id),
                    "filename": file.original_filename,
                    "file_type": file.file_type,
                    "month": file.month,
                    "validation_status": "valid" if file.upload_status == "uploaded" else "failed",
                    "upload_status": file.upload_status,
                    "file_size": file.file_size,
                    "created_at": file.created_at.isoformat(),
                    "validation_errors": file.validation_errors or []
                }
                for file in files
            ],
            "total": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )

@router.delete("/file/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete uploaded file"""
    try:
        # Get file and verify ownership through project
        file_upload = db.query(FileUpload).join(GSTProject).filter(
            FileUpload.id == file_id,
            GSTProject.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # TODO: Delete actual file from storage
        
        db.delete(file_upload)
        db.commit()
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

@router.post("/analyze/{project_id}")
async def analyze_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger GST analysis for project"""
    try:
        # Verify project ownership
        project = db.query(GSTProject).filter(
            GSTProject.id == project_id,
            GSTProject.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if files are uploaded and validated
        files = db.query(FileUpload).filter(
            FileUpload.project_id == project_id,
            FileUpload.validation_status == 'valid'
        ).all()
        
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid files found for analysis"
            )
        
        # Trigger analysis
        analysis_result = GSTAnalysisService.start_analysis(
            db=db,
            project_id=project_id
        )
        
        if not analysis_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=analysis_result.get("error", "Analysis failed")
            )
        
        # Update project status
        project.status = 'analyzed'
        db.commit()
        
        return {
            "message": "Analysis completed successfully",
            "analysis_result": {
                "id": analysis_result.get("analysis_id"),
                "output_filename": analysis_result.get("output_filename"),
                "analysis_summary": analysis_result.get("summary")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze project: {str(e)}"
        )

@router.get("/analysis/{project_id}")
async def get_analysis_results(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis results for project"""
    try:
        # Verify project ownership
        project = db.query(GSTProject).filter(
            GSTProject.id == project_id,
            GSTProject.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get analysis results
        analysis_results = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id
        ).order_by(AnalysisResult.created_at.desc()).all()
        
        return {
            "analysis_results": [
                {
                    "id": str(result.id),
                    "status": result.status,
                    "output_filename": result.output_filename,
                    "output_file_path": result.output_file_path,
                    "analysis_summary": result.analysis_summary,
                    "created_at": result.created_at.isoformat(),
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None
                }
                for result in analysis_results
            ],
            "total": len(analysis_results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis results: {str(e)}"
        )

@router.get("/analysis")
async def get_all_analysis_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all analysis results for current user across all projects"""
    try:
        print(f"Getting analysis results for user: {current_user.email}")
        
        # Get all analysis results for user's projects
        analysis_results = db.query(AnalysisResult).join(
            GSTProject, AnalysisResult.project_id == GSTProject.id
        ).filter(
            GSTProject.user_id == current_user.id
        ).order_by(AnalysisResult.created_at.desc()).all()
        
        print(f"Found {len(analysis_results)} analysis results")
        
        result_list = []
        for result in analysis_results:
            try:
                # Get project separately to avoid join issues
                project = db.query(GSTProject).filter(GSTProject.id == result.project_id).first()
                
                result_dict = {
                    "id": str(result.id),
                    "project_id": str(result.project_id),
                    "project_name": project.name if project else "Unknown Project",
                    "status": result.status,
                    "output_filename": result.output_filename,
                    "output_file_path": result.output_file_path,
                    "analysis_summary": result.analysis_summary,
                    "error_message": getattr(result, 'error_message', None),
                    "created_at": result.created_at.isoformat(),
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None
                }
                result_list.append(result_dict)
            except Exception as e:
                print(f"Error processing result {result.id}: {str(e)}")
                continue
        
        print(f"Successfully processed {len(result_list)} results")
        
        return {
            "analysis_results": result_list,
            "total": len(result_list)
        }
        
    except Exception as e:
        print(f"Error in get_all_analysis_results: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get all analysis results: {str(e)}"
        )

@router.get("/download-analysis/{analysis_id}")
async def download_analysis_result(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download analysis result Excel file"""
    try:
        # Get analysis result
        analysis = db.query(AnalysisResult).filter(
            AnalysisResult.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis result not found"
            )
        
        # Verify project ownership
        project = db.query(GSTProject).filter(
            GSTProject.id == analysis.project_id,
            GSTProject.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        
        # Check if file exists
        file_path = Path(analysis.output_file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis file not found on disk"
            )
        
        # Return file download response
        return FileResponse(
            path=str(file_path),
            filename=analysis.output_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download analysis result: {str(e)}"
        )
