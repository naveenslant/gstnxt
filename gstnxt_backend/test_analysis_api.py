#!/usr/bin/env python3
"""
Test analysis results API
"""

import sys
sys.path.append('.')

from app.database import get_db
from app.models import AnalysisResult
from sqlalchemy.orm import Session

def test_analysis_results():
    db: Session = next(get_db())
    try:
        # Get all analysis results
        results = db.query(AnalysisResult).all()
        print(f"Found {len(results)} analysis results")
        
        for result in results[:3]:  # Show first 3
            print(f"\nAnalysis Result:")
            print(f"  ID: {result.id}")
            print(f"  Status: {result.status}")
            print(f"  Output filename: {result.output_filename}")
            print(f"  Output path: {result.output_file_path}")
            print(f"  Analysis summary: {result.analysis_summary}")
            print(f"  Created: {result.created_at}")
            print(f"  Completed: {result.completed_at}")
            
            # Test API response format
            api_response = {
                "id": str(result.id),
                "status": result.status,
                "output_filename": result.output_filename,
                "output_file_path": result.output_file_path,
                "analysis_summary": result.analysis_summary,
                "created_at": result.created_at.isoformat(),
                "completed_at": result.completed_at.isoformat() if result.completed_at else None
            }
            print(f"  API format: {api_response}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_analysis_results()
