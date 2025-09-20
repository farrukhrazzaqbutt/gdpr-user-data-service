"""
SQLAlchemy models for GDPR-aware User Data Service
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base
import enum


class DeletionState(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    pii_encrypted = Column(Text, nullable=True)  # Encrypted JSON blob
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    consents = relationship("Consent", back_populates="user", cascade="all, delete-orphan")
    deletion_requests = relationship("DeletionRequest", back_populates="user", cascade="all, delete-orphan")


class Consent(Base):
    __tablename__ = "consents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    purpose = Column(String(255), nullable=False)  # e.g., "marketing", "analytics", "essential"
    granted = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="consents")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(255), nullable=False)  # User ID or system
    action = Column(String(100), nullable=False)  # e.g., "create", "update", "delete", "rtbf"
    subject_type = Column(String(50), nullable=False)  # e.g., "user", "consent"
    subject_id = Column(Integer, nullable=False)
    details_json = Column(Text, nullable=True)  # Additional context
    ts = Column(DateTime(timezone=True), server_default=func.now())
    
    # Index for efficient querying
    __table_args__ = (
        {"postgresql_partition_by": "RANGE (ts)"} if hasattr(Base, 'metadata') else None
    )


class DeletionRequest(Base):
    __tablename__ = "deletion_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    state = Column(Enum(DeletionState), default=DeletionState.PENDING, nullable=False)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="deletion_requests")
