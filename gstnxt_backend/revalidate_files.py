#!/usr/bin/env python3
"""
Re-validate all uploaded files with updated patterns
"""

import sys
sys.path.append('.')

from app.database import get_db
from app.models import FileUpload
from app.services.file_validation_service import FileValidationService
from sqlalchemy.orm import Session

def re_validate_files():
    db: Session = next(get_db())
    try:
        # Get all uploaded files
        files = db.query(FileUpload).all()
        print(f"Found {len(files)} files to re-validate")
        
        for file in files:
            print(f"\nRe-validating: {file.original_filename}")
            
            # Determine file type from filename
            file_type = None
            if file.original_filename.startswith('GSTR1'):
                file_type = 'GSTR1'
            elif file.original_filename.startswith('GSTR3B'):
                file_type = 'GSTR3B'
            elif 'R2A' in file.original_filename:
                file_type = 'GSTR2A'  # R2A files are GSTR2A files
            elif 'GSTR' in file.original_filename.upper():
                # Try to extract GSTR type from filename
                if '2A' in file.original_filename.upper():
                    file_type = 'GSTR2A'
                elif '3B' in file.original_filename.upper():
                    file_type = 'GSTR3B'
                elif '1' in file.original_filename.upper():
                    file_type = 'GSTR1'
            
            if file_type:
                # Validate filename
                validation_result = FileValidationService.validate_filename(
                    file.original_filename, 
                    file_type
                )
                
                # Update validation status
                if validation_result.get('is_valid', False):
                    file.validation_status = 'valid'
                    file.validation_error = None
                    print(f"  ✅ Valid - {validation_result.get('details', {})}")
                else:
                    file.validation_status = 'invalid'
                    file.validation_error = validation_result.get('error', 'Unknown error')
                    print(f"  ❌ Invalid - {file.validation_error}")
            else:
                file.validation_status = 'invalid'
                file.validation_error = 'Unknown file type'
                print(f"  ❌ Unknown file type")
        
        db.commit()
        print(f"\n✅ Re-validation complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    re_validate_files()
