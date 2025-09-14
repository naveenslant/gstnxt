#!/usr/bin/env python3
"""
Test analysis functionality
"""

import sys
sys.path.append('.')

from app.database import get_db
from app.models import GSTProject, FileUpload
from app.services.gst_analysis_service import GSTAnalysisService
from sqlalchemy.orm import Session

def test_analysis():
    db: Session = next(get_db())
    try:
        # Get first project that has valid files
        project = db.query(GSTProject).first()
        if not project:
            print("❌ No projects found")
            return
        
        print(f"Testing analysis for project: {project.project_name}")
        print(f"Project ID: {project.id}")
        
        # Check valid files
        valid_files = db.query(FileUpload).filter(
            FileUpload.project_id == project.id,
            FileUpload.validation_status == 'valid'
        ).all()
        
        print(f"Valid files found: {len(valid_files)}")
        for file in valid_files:
            print(f"  - {file.original_filename} ({file.file_type})")
        
        if valid_files:
            print("\n🔄 Starting analysis...")
            result = GSTAnalysisService.start_analysis(db, str(project.id))
            
            if result.get("success"):
                print("✅ Analysis completed successfully!")
                print(f"Analysis ID: {result.get('analysis_id')}")
                print(f"Output file: {result.get('output_filename')}")
                if result.get('summary'):
                    print(f"Summary: {result.get('summary')}")
            else:
                print(f"❌ Analysis failed: {result.get('error')}")
        else:
            print("❌ No valid files to analyze")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_analysis()
