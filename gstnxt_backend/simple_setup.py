#!/usr/bin/env python3
"""
Simple database setup script for GST Next application
Creates database, tables, and demo user in one go
"""

import sys
import os
sys.path.append('.')

from app.database import engine, SessionLocal
from app.models import Base, User
from app.services.auth_service import AuthService

def setup_database():
    """Create tables and demo user"""
    print("Creating database tables...")
    
    # Create all tables
    Base.metadata.drop_all(bind=engine)  # Drop existing tables
    Base.metadata.create_all(bind=engine)  # Create fresh tables
    print("✅ Tables created successfully")
    
    # Create demo user
    print("Creating demo user...")
    
    db = SessionLocal()
    try:
        # Hash the password
        hashed_password = AuthService.hash_password("demo123")
        
        # Create demo user
        demo_user = User(
            email="demo@gstnxt.com",
            password_hash=hashed_password,
            full_name="Demo User",
            company_name="Demo Company",
            gstin="24AABCU9603R1ZV",
            phone="9876543210",
            user_type="ca",
            is_active=True,
            is_verified=True,
            subscription_type="demo"
        )
        
        db.add(demo_user)
        db.commit()
        print("✅ Demo user created successfully")
        print("📧 Email: demo@gstnxt.com")
        print("🔐 Password: demo123")
        
    except Exception as e:
        print(f"❌ Error creating demo user: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up GST Next database...")
    
    if setup_database():
        print("✅ Database setup completed successfully!")
        print("🎯 Ready to start the application!")
    else:
        print("❌ Database setup failed!")
        sys.exit(1)
