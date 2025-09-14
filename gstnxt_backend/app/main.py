"""
GST Next FastAPI Application
Main application entry point
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import database
from app.database import SessionLocal

# Import API routes
from app.api.routes import auth, projects, files, gstin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting GST Next API...")
    yield
    # Shutdown
    print("💤 Shutting down GST Next API...")

# Create FastAPI application
app = FastAPI(
    title="GST Next API",
    description="Comprehensive GST Analysis and Compliance Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://gstnxt.slantaxiom.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(gstin.router, prefix="/api/gstin", tags=["GSTIN"])

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "GST Next API is running!",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "GST Next API is operational"}

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
