from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User, GSTProject
from app.services.file_validation_service import FileValidationService

router = APIRouter()

class CreateProjectRequest(BaseModel):
    project_name: str
    gstin: str
    financial_year: str  # 2020-21

class ProjectResponse(BaseModel):
    id: str
    project_name: str
    gstin: str
    financial_year: str
    status: str
    created_at: str

@router.post("/create", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new GST project"""
    try:
        # Create project
        project = GSTProject(
            user_id=current_user.id,
            project_name=request.project_name,
            gstin=request.gstin.upper().strip(),
            financial_year=request.financial_year,
            status='created'
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        return ProjectResponse(
            id=str(project.id),
            project_name=project.project_name,
            gstin=project.gstin,
            financial_year=project.financial_year,
            status=project.status,
            created_at=project.created_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.get("/list")
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's projects"""
    try:
        projects = db.query(GSTProject).filter(
            GSTProject.user_id == current_user.id
        ).order_by(GSTProject.created_at.desc()).all()
        
        return {
            "projects": [
                {
                    "id": str(project.id),
                    "project_name": project.project_name,
                    "gstin": project.gstin,
                    "financial_year": project.financial_year,
                    "status": project.status,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat() if project.updated_at else None
                }
                for project in projects
            ],
            "total": len(projects)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project details"""
    try:
        project = db.query(GSTProject).filter(
            GSTProject.id == project_id,
            GSTProject.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get upload status
        upload_status = FileValidationService.get_upload_status(db, project_id)
        
        return {
            "project": {
                "id": str(project.id),
                "project_name": project.project_name,
                "gstin": project.gstin,
                "financial_year": project.financial_year,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat() if project.updated_at else None
            },
            "upload_status": upload_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}"
        )

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete project"""
    try:
        project = db.query(GSTProject).filter(
            GSTProject.id == project_id,
            GSTProject.user_id == current_user.id
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # TODO: Delete associated files from storage
        
        db.delete(project)
        db.commit()
        
        return {"message": "Project deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

@router.get("/{project_id}/upload-status")
async def get_upload_status(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get upload status for project"""
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
        
        # Get upload status
        upload_status = FileValidationService.get_upload_status(db, project_id)
        
        return upload_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upload status: {str(e)}"
        )
