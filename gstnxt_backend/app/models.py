from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    company_name = Column(String(200))
    gstin = Column(String(15))
    phone = Column(String(20))
    user_type = Column(String(50), default='ca')  # ca, inspector, taxpayer
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    subscription_type = Column(String(50), default='demo')  # demo, basic, premium
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    projects = relationship("GSTProject", back_populates="user")

class GSTProject(Base):
    __tablename__ = "gst_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_name = Column(String(200), nullable=False)
    gstin = Column(String(15), nullable=False)
    financial_year = Column(String(10), nullable=False)  # 2020-21
    status = Column(String(50), default='created')  # created, uploading, analyzing, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="projects")
    uploads = relationship("FileUpload", back_populates="project")
    analyses = relationship("AnalysisResult", back_populates="project")

class FileUpload(Base):
    __tablename__ = "file_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("gst_projects.id"), nullable=False)
    file_type = Column(String(20), nullable=False)  # GSTR1, GSTR2A
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    upload_status = Column(String(50), default='uploaded')  # uploaded, validated, processed, error
    validation_status = Column(String(50), default='pending')  # pending, valid, invalid
    validation_error = Column(Text)  # Single validation error message
    validation_errors = Column(JSON)  # Detailed validation errors
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("GSTProject", back_populates="uploads")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("gst_projects.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # comparison, validation, reconciliation
    output_filename = Column(String(500))
    output_file_path = Column(String(1000))
    analysis_summary = Column(JSON)
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    project = relationship("GSTProject", back_populates="analyses")

class GSTINValidation(Base):
    __tablename__ = "gstin_validations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gstin = Column(String(15), nullable=False, index=True)
    is_valid = Column(Boolean, nullable=False)
    validation_details = Column(JSON)
    validated_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(50))

class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
