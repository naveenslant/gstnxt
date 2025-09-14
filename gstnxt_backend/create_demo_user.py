#!/usr/bin/env python3
"""
Manual Demo User Creation Script
Run this after the server has started to create the demo user.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.auth_service import AuthService
from app.models import User

def create_demo_user():
    """Create demo user manually"""
    db = SessionLocal()
    try:
        # Check if demo user exists
        demo_user = db.query(User).filter(User.email == "demo@gstnxt.com").first()
        if demo_user:
            print("✅ Demo user already exists!")
            return
        
        # Create demo user
        demo_user_data = {
            "username": "demo_user",
            "email": "demo@gstnxt.com", 
            "password": "demo123",
            "full_name": "Demo User",
            "company_name": "Demo Company",
            "user_type": "ca"
        }
        
        demo_user = AuthService.create_user(db, demo_user_data)
        print("✅ Demo user created successfully!")
        print("📧 Email: demo@gstnxt.com")
        print("🔑 Password: demo123")
        
    except Exception as e:
        print(f"❌ Error creating demo user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_user()
