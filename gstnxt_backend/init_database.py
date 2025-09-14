#!/usr/bin/env python3
"""
Manual Table Creation Script
Run this to create database tables manually.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models import User, GSTProject, FileUpload, AnalysisResult, GSTINValidation, SystemConfig
from app.services.auth_service import AuthService
from app.database import SessionLocal

def create_tables_and_demo_user():
    """Create tables and demo user"""
    try:
        print("🔧 Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Create demo user
        print("👤 Creating demo user...")
        db = SessionLocal()
        try:
            # Check if demo user exists
            demo_user = db.query(User).filter(User.email == "demo@gstnxt.com").first()
            if demo_user:
                print("✅ Demo user already exists!")
            else:
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
            print(f"❌ Error with demo user: {e}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    create_tables_and_demo_user()
