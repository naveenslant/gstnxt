"""
File Upload Router
Handles file uploads and management for GST analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import shutil
import aiofiles
from datetime import datetime

from app.database import get_db
from app.models import FileUpload, User, GSTProject
from app.services.auth_service import AuthService

router = APIRouter()

# Upload directory
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload/{project_id}")
async def upload_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload files to a project"""
    
    # Verify project exists and belongs to user
    project = db.query(GSTProject).filter(
        GSTProject.id == project_id,
        GSTProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    uploaded_files = []
    
    for file in files:
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{file_id}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Save file to disk
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Create database record
            file_record = FileUpload(
                id=file_id,
                project_id=project_id,
                filename=file.filename,
                file_path=file_path,
                file_size=len(content),
                file_type=file.content_type,
                upload_status='uploaded'
            )
            
            db.add(file_record)
            uploaded_files.append({
                "id": file_id,
                "filename": file.filename,
                "size": len(content),
                "type": file.content_type
            })
            
        except Exception as e:
            # Clean up file if database save fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )
    
    # Commit all files at once
    db.commit()
    
    return {
        "message": f"Successfully uploaded {len(uploaded_files)} files",
        "files": uploaded_files
    }

@router.get("/files/{project_id}")
async def get_project_files(
    project_id: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all files for a project"""
    
    # Verify project exists and belongs to user
    project = db.query(GSTProject).filter(
        GSTProject.id == project_id,
        GSTProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get all files for the project
    files = db.query(FileUpload).filter(
        FileUpload.project_id == project_id
    ).all()
    
    return {
        "files": [
            {
                "id": str(file.id),
                "filename": file.filename,
                "file_size": file.file_size,
                "file_type": file.file_type,
                "upload_status": file.upload_status,
                "uploaded_at": file.uploaded_at.isoformat() if file.uploaded_at else None,
                "analysis_status": file.analysis_status
            }
            for file in files
        ]
    }

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a file"""
    
    # Get file record
    file_record = db.query(FileUpload).filter(FileUpload.id == file_id).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Verify file belongs to user's project
    project = db.query(GSTProject).filter(
        GSTProject.id == file_record.project_id,
        GSTProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete file from disk
    if os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)
    
    # Delete database record
    db.delete(file_record)
    db.commit()
    
    return {"message": "File deleted successfully"}

@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Download a file"""
    
    # Get file record
    file_record = db.query(FileUpload).filter(FileUpload.id == file_id).first()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Verify file belongs to user's project
    project = db.query(GSTProject).filter(
        GSTProject.id == file_record.project_id,
        GSTProject.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if file exists on disk
    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.filename,
        media_type=file_record.file_type
    )
