#!/usr/bin/env python3
"""
Test filename validation with actual uploaded file
"""

import sys
sys.path.append('.')

from app.services.file_validation_service import FileValidationService

# Test with actual filename from the upload
test_filename = "GSTR1_29AABCE5725G1ZN_122021_Inv.zip"
file_type = "GSTR1"

print(f"Testing filename: {test_filename}")
print(f"File type: {file_type}")

result = FileValidationService.validate_filename(test_filename, file_type)

print(f"Is Valid: {result.get('is_valid', False)}")
if result.get('is_valid', False):
    print(f"Details: {result.get('details', {})}")
else:
    print(f"Error: {result.get('error', 'Unknown error')}")
    print(f"Details: {result.get('details', {})}")
