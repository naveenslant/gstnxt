#!/usr/bin/env python3
"""
Database setup script for GST Next application
Creates the PostgreSQL database and tables
"""

import psycopg2
from psycopg2 import sql
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    """Create the PostgreSQL database"""
    try:
        # Connect to PostgreSQL server (not to specific database)
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="postgres"  # Connect to default postgres database
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", ("gstnxt_db",))
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier("gstnxt_db")
            ))
            logger.info("Database 'gstnxt_db' created successfully")
        else:
            logger.info("Database 'gstnxt_db' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Failed to create database: {e}")
        return False

def create_tables():
    """Create the application tables"""
    try:
        # Import after database creation
        sys.path.append('.')
        from app.database import engine, Base
        from app.models import User, GSTProject, FileUpload, AnalysisResult, GSTINValidation, SystemConfig
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

def create_demo_user():
    """Create demo user for testing"""
    try:
        from app.database import SessionLocal
        from app.services.auth_service import AuthService
        from app.models import User
        import time
        
        # Wait a moment for tables to be fully committed
        time.sleep(1)
        
        db = SessionLocal()
        
        try:
            # Check if demo user exists
            demo_user = db.query(User).filter(User.email == "demo@gstnxt.com").first()
            if not demo_user:
                # Hash the password
                hashed_password = AuthService.hash_password("demo123")
                
                # Create demo user directly
                demo_user = User(
                    email="demo@gstnxt.com",
                    password_hash=hashed_password,
                    full_name="Demo User",
                    company_name="Demo Company",
                    gstin="24AABCU9603R1ZV",
                    phone="9876543210",
                    user_type="ca"
                )
                
                db.add(demo_user)
                db.commit()
                logger.info("Demo user created successfully")
            else:
                logger.info("Demo user already exists")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create demo user: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("Starting GST Next database setup...")
    
    # Step 1: Create database
    if not create_database():
        logger.error("Database creation failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Create tables
    if not create_tables():
        logger.error("Table creation failed. Exiting.")
        sys.exit(1)
    
    # Step 3: Create demo user
    if not create_demo_user():
        logger.error("Demo user creation failed. Exiting.")
        sys.exit(1)
    
    logger.info("✅ GST Next database setup completed successfully!")
    logger.info("📊 Database: gstnxt_db")
    logger.info("👤 Demo User: demo@gstnxt.com / demo123")
    logger.info("🚀 Ready to start the application!")

if __name__ == "__main__":
    main()
