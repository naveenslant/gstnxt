#!/usr/bin/env python3
"""
Test GSTIN validation with the user's GSTIN
"""

import sys
sys.path.append('.')

from app.services.gstin_validator import GSTINValidator

# Test the user's GSTIN
test_gstin = "29AABCE5725G1ZN"

print(f"Testing GSTIN: {test_gstin}")
result = GSTINValidator.validate_gstin(test_gstin)

print(f"Is Valid: {result['is_valid']}")
if result['is_valid']:
    print(f"State: {result['details']['state_name']}")
    print(f"Details: {result['details']}")
else:
    print(f"Error: {result['error']}")
    print(f"Details: {result['details']}")
