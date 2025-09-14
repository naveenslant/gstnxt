from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.database import engine, Base, SessionLocal
from app.api.routes import auth, gstin, projects, files
from app.services.auth_service import AuthService
from app.models import User


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_user():
    """Create demo user if it doesn't exist"""
    import time
    # Small delay to ensure tables are fully created
    time.sleep(0.5)
    
    db = SessionLocal()
    try:
        # Check if demo user exists
        demo_user = db.query(User).filter(User.email == "demo@gstnxt.com").first()
        if not demo_user:
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
            logger.info("Demo user created successfully")
        else:
            logger.info("Demo user already exists")
    except Exception as e:
        logger.error(f"Failed to create demo user: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting GST Next Application...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create demo user
        create_demo_user()
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down GST Next Application...")


# Create FastAPI app
app = FastAPI(
    title="GST Next API",
    description="Backend API for GST analysis and file processing",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "gstnxt-backend",
        "version": "1.0.0"
    }


# API route includes
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    gstin.router,
    prefix="/api/gstin",
    tags=["GSTIN Validation"]
)

app.include_router(
    projects.router,
    prefix="/api/projects",
    tags=["Project Management"]
)

app.include_router(
    files.router,
    prefix="/api/files",
    tags=["File Management"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GST Next Backend API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
