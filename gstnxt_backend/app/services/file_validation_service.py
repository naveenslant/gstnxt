import os
import re
import zipfile
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
import uuid
from sqlalchemy.orm import Session

from app.models import GSTProject, FileUpload

class FileValidationService:
    """Service for validating uploaded GST files"""
    
    VALID_EXTENSIONS = ['.xlsx', '.xls', '.zip']
    GSTR1_PATTERN = r'GSTR1_([A-Z0-9]{15})_(\d{6})_Inv(?:_(\d+))?(?:\.zip)?'
    GSTR2A_PATTERN = r'([A-Z0-9]{15})_(\d{6})_R2A(?:\.zip)?'
    
    @staticmethod
    def validate_filename(filename: str, file_type: str) -> Dict[str, Any]:
        """Validate filename format and extract metadata"""
        
        if file_type == "GSTR1":
            match = re.match(FileValidationService.GSTR1_PATTERN, filename)
            if not match:
                return {
                    "is_valid": False,
                    "error": "Invalid GSTR1 filename format. Expected: GSTR1_GSTIN_MMYYYY_Inv[_Number]",
                    "details": {}
                }
            
            gstin, period, inv_number = match.groups()
            inv_number = inv_number or "1"  # Default invoice number if not provided
            
        elif file_type == "GSTR2A":
            match = re.match(FileValidationService.GSTR2A_PATTERN, filename)
            if not match:
                return {
                    "is_valid": False,
                    "error": "Invalid GSTR2A filename format. Expected: GSTIN_MMYYYY_R2A",
                    "details": {}
                }
            
            gstin, period = match.groups()
            inv_number = None
            
        else:
            return {
                "is_valid": False,
                "error": f"Unsupported file type: {file_type}",
                "details": {}
            }
        
        # Parse period (MMYYYY)
        try:
            month = int(period[:2])
            year = int(period[2:])
            
            if month < 1 or month > 12:
                return {
                    "is_valid": False,
                    "error": f"Invalid month in filename: {month}",
                    "details": {"period": period}
                }
            
            if year < 2017 or year > 2030:
                return {
                    "is_valid": False,
                    "error": f"Invalid year in filename: {year}",
                    "details": {"period": period}
                }
                
        except ValueError:
            return {
                "is_valid": False,
                "error": f"Invalid period format: {period}",
                "details": {"period": period}
            }
        
        return {
            "is_valid": True,
            "error": None,
            "details": {
                "gstin": gstin,
                "month": month,
                "year": year,
                "period": period,
                "inv_number": inv_number,
                "file_type": file_type
            }
        }
    
    @staticmethod
    def extract_zip_file(zip_path: str, extract_to: str) -> Dict[str, Any]:
        """Extract ZIP file and return list of extracted files"""
        try:
            extracted_files = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if not file_info.is_dir():
                        # Extract file
                        zip_ref.extract(file_info, extract_to)
                        extracted_path = os.path.join(extract_to, file_info.filename)
                        
                        # Get file extension
                        file_ext = Path(file_info.filename).suffix.lower()
                        
                        if file_ext in FileValidationService.VALID_EXTENSIONS:
                            extracted_files.append({
                                "filename": file_info.filename,
                                "path": extracted_path,
                                "size": file_info.file_size
                            })
            
            return {
                "success": True,
                "extracted_files": extracted_files,
                "total_files": len(extracted_files)
            }
            
        except zipfile.BadZipFile:
            return {
                "success": False,
                "error": "Invalid ZIP file",
                "extracted_files": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error extracting ZIP file: {str(e)}",
                "extracted_files": []
            }
    
    @staticmethod
    def validate_excel_file(file_path: str) -> Dict[str, Any]:
        """Validate Excel file structure and content"""
        try:
            # Read Excel file
            excel_file = pd.ExcelFile(file_path)
            
            # Get sheet names
            sheet_names = excel_file.sheet_names
            
            # Basic validation
            if not sheet_names:
                return {
                    "is_valid": False,
                    "error": "Excel file has no sheets",
                    "details": {}
                }
            
            # Check for common GST sheet names
            gst_sheets = []
            for sheet in sheet_names:
                if any(keyword in sheet.upper() for keyword in ['B2B', 'B2C', 'EXPORT', 'CDNR', 'HSN']):
                    gst_sheets.append(sheet)
            
            return {
                "is_valid": True,
                "error": None,
                "details": {
                    "total_sheets": len(sheet_names),
                    "sheet_names": sheet_names,
                    "gst_sheets": gst_sheets,
                    "file_path": file_path
                }
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Error reading Excel file: {str(e)}",
                "details": {"file_path": file_path}
            }
    
    @staticmethod
    def get_upload_status(db: Session, project_id: str) -> Dict[str, Any]:
        """Get upload status for a project"""
        uploads = db.query(FileUpload).filter(
            FileUpload.project_id == project_id
        ).all()
        
        # Initialize month status
        months = {
            'GSTR1': {i: False for i in range(1, 13)},
            'GSTR2A': {i: False for i in range(1, 13)}
        }
        
        # Mark uploaded months
        for upload in uploads:
            if upload.file_type in months and upload.upload_status == 'uploaded':
                months[upload.file_type][upload.month] = True
        
        # Calculate completion percentage
        gstr1_uploaded = sum(1 for uploaded in months['GSTR1'].values() if uploaded)
        gstr2a_uploaded = sum(1 for uploaded in months['GSTR2A'].values() if uploaded)
        
        total_possible = 24  # 12 months each for GSTR1 and GSTR2A
        total_uploaded = gstr1_uploaded + gstr2a_uploaded
        completion_percentage = (total_uploaded / total_possible) * 100
        
        return {
            "months": months,
            "summary": {
                "gstr1_uploaded": gstr1_uploaded,
                "gstr2a_uploaded": gstr2a_uploaded,
                "total_uploaded": total_uploaded,
                "completion_percentage": round(completion_percentage, 2)
            },
            "uploads": [
                {
                    "id": str(upload.id),
                    "file_type": upload.file_type,
                    "month": upload.month,
                    "year": upload.year,
                    "filename": upload.original_filename,
                    "status": upload.upload_status,
                    "created_at": upload.created_at.isoformat()
                }
                for upload in uploads
            ]
        }
    
    @staticmethod
    def save_upload_record(
        db: Session,
        project_id: str,
        file_type: str,
        month: int,
        year: int,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_size: int
    ) -> FileUpload:
        """Save file upload record to database"""
        
        # Check if file already exists for this month
        existing_upload = db.query(FileUpload).filter(
            FileUpload.project_id == project_id,
            FileUpload.file_type == file_type,
            FileUpload.month == month,
            FileUpload.year == year
        ).first()
        
        if existing_upload:
            # Update existing record
            existing_upload.original_filename = original_filename
            existing_upload.stored_filename = stored_filename
            existing_upload.file_path = file_path
            existing_upload.file_size = file_size
            existing_upload.upload_status = 'uploaded'
            db.commit()
            db.refresh(existing_upload)
            return existing_upload
        else:
            # Create new record
            upload = FileUpload(
                project_id=project_id,
                file_type=file_type,
                month=month,
                year=year,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=file_size,
                upload_status='uploaded'
            )
            
            db.add(upload)
            db.commit()
            db.refresh(upload)
            return upload

    @staticmethod
    async def validate_and_store_file(
        db: Session,
        project_id: str,
        filename: str,
        content: bytes,
        gstin: str
    ) -> Dict[str, Any]:
        """Validate and store uploaded file"""
        
        # Determine file type from filename
        file_type = "unknown"
        if "GSTR1" in filename.upper():
            file_type = "GSTR1"
        elif "GSTR2A" in filename.upper() or "R2A" in filename.upper():
            file_type = "GSTR2A"
        
        # Validate filename format
        validation_result = FileValidationService.validate_filename(filename, file_type)
        
        validation_status = "valid" if validation_result.get("is_valid", False) else "failed"
        month = validation_result.get("details", {}).get("month", "")
        
        # Generate unique file ID and path
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1]
        stored_filename = f"{file_id}{file_extension}"
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, stored_filename)
        
        # Save file to disk
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Create database record
        file_upload = FileUpload(
            id=uuid.UUID(file_id),
            project_id=uuid.UUID(project_id),
            original_filename=filename,
            stored_filename=stored_filename,
            file_type=file_type,
            month=int(month) if month and str(month).isdigit() else 1,
            year=2024,  # Default year, should be extracted from filename
            upload_status="uploaded" if validation_status == "valid" else "error",
            file_size=len(content),
            file_path=file_path,
            validation_errors=[] if validation_status == "valid" else [validation_result.get("error", "Validation failed")]
        )
        
        db.add(file_upload)
        db.commit()
        db.refresh(file_upload)
        
        return {
            "file_upload": file_upload,
            "filename": filename,
            "file_type": file_type,
            "month": f"{month:02d}" if isinstance(month, int) else str(month),
            "validation_status": validation_status,
            "upload_status": "uploaded",
            "validation_errors": [] if validation_status == "valid" else [validation_result.get("error", "Validation failed")]
        }
