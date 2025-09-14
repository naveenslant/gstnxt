from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from decouple import config

# Database URL - PostgreSQL for production
DATABASE_URL = config('DATABASE_URL', default='postgresql://postgres:postgres@localhost:5432/gstnxt_db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=config('DATABASE_ECHO', default=False, cast=bool)
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)
