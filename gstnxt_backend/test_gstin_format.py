#!/usr/bin/env python3
"""
Test GSTIN validation without check digit verification
"""

import sys
import re
sys.path.append('.')

from app.services.gstin_validator import GSTINValidator

def test_gstin_format_only(gstin: str):
    """Test only the format validation part"""
    if not gstin:
        return False, "GSTIN is required"
    
    # Remove spaces and convert to uppercase
    gstin = gstin.strip().upper()
    
    # Basic format validation
    if len(gstin) != 15:
        return False, f"GSTIN must be 15 characters long, got {len(gstin)}"
    
    # Pattern validation - GSTIN format: 99AAAAA9999A9AZ (last character can be letter or digit)
    gstin_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9][A-Z][A-Z0-9]$'
    if not re.match(gstin_pattern, gstin):
        return False, "Invalid GSTIN format pattern"
    
    return True, "Format is valid"

# Test the user's GSTIN
test_gstin = "29AABCE5725G1ZN"

print(f"Testing GSTIN format: {test_gstin}")
is_valid, message = test_gstin_format_only(test_gstin)

print(f"Format Valid: {is_valid}")
print(f"Message: {message}")

if is_valid:
    # Extract components to verify parsing
    state_code = test_gstin[:2]
    pan = test_gstin[2:12]
    entity_number = test_gstin[12]
    check_digit = test_gstin[13]
    additional_code = test_gstin[14]
    
    print(f"State Code: {state_code}")
    print(f"PAN: {pan}")
    print(f"Entity Number: {entity_number}")
    print(f"Check Digit: {check_digit}")
    print(f"Additional Code: {additional_code}")
    
    # Test with known valid Karnataka GSTIN
    print("\n" + "="*50)
    print("Testing with a known valid Karnataka GSTIN:")
    valid_gstin = "29AAPCU1681L1Z5"  # Known valid GSTIN
    result = GSTINValidator.validate_gstin(valid_gstin)
    print(f"GSTIN: {valid_gstin}")
    print(f"Is Valid: {result['is_valid']}")
    if result['is_valid']:
        print(f"State: {result['details']['state_name']}")
    else:
        print(f"Error: {result['error']}")
