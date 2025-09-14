from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.services.gstin_validator import GSTINValidator
from app.models import GSTINValidation

router = APIRouter()

class GSTINValidateRequest(BaseModel):
    gstin: str

class GSTINValidateResponse(BaseModel):
    gstin: str
    is_valid: bool
    error: Optional[str]
    details: dict
    state_name: Optional[str] = None

@router.post("/validate", response_model=GSTINValidateResponse)
async def validate_gstin(
    request: GSTINValidateRequest, 
    db: Session = Depends(get_db)
):
    """Validate GSTIN number"""
    try:
        # Validate GSTIN
        validation_result = GSTINValidator.validate_gstin(request.gstin)
        
        # Save validation record
        validation_record = GSTINValidation(
            gstin=request.gstin.upper().strip(),
            is_valid=validation_result["is_valid"],
            validation_details=validation_result
        )
        
        db.add(validation_record)
        db.commit()
        
        return GSTINValidateResponse(
            gstin=request.gstin.upper().strip(),
            is_valid=validation_result["is_valid"],
            error=validation_result["error"],
            details=validation_result["details"],
            state_name=validation_result["details"].get("state_name") if validation_result["is_valid"] else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GSTIN validation failed: {str(e)}"
        )

@router.get("/validate/{gstin}")
async def validate_gstin_get(gstin: str, db: Session = Depends(get_db)):
    """Validate GSTIN number via GET request"""
    try:
        # Check cache first
        cached_validation = db.query(GSTINValidation).filter(
            GSTINValidation.gstin == gstin.upper().strip()
        ).order_by(GSTINValidation.validated_at.desc()).first()
        
        if cached_validation:
            return {
                "gstin": cached_validation.gstin,
                "is_valid": cached_validation.is_valid,
                "details": cached_validation.validation_details.get("details", {}),
                "state_name": cached_validation.validation_details.get("details", {}).get("state_name"),
                "cached": True,
                "validated_at": cached_validation.validated_at.isoformat()
            }
        
        # Perform fresh validation
        validation_result = GSTINValidator.validate_gstin(gstin)
        
        # Save validation record
        validation_record = GSTINValidation(
            gstin=gstin.upper().strip(),
            is_valid=validation_result["is_valid"],
            validation_details=validation_result
        )
        
        db.add(validation_record)
        db.commit()
        
        return {
            "gstin": gstin.upper().strip(),
            "is_valid": validation_result["is_valid"],
            "error": validation_result["error"],
            "details": validation_result["details"],
            "state_name": validation_result["details"].get("state_name") if validation_result["is_valid"] else None,
            "cached": False
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GSTIN validation failed: {str(e)}"
        )

@router.get("/history")
async def get_validation_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent GSTIN validation history"""
    try:
        validations = db.query(GSTINValidation).order_by(
            GSTINValidation.validated_at.desc()
        ).limit(limit).all()
        
        return {
            "validations": [
                {
                    "gstin": val.gstin,
                    "is_valid": val.is_valid,
                    "validated_at": val.validated_at.isoformat(),
                    "state": val.validation_details.get("details", {}).get("state_name"),
                    "ip_address": val.ip_address
                }
                for val in validations
            ],
            "total": len(validations)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation history: {str(e)}"
        )
