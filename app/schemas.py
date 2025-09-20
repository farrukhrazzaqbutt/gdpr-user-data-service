"""
Pydantic schemas for API validation and serialization
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models import DeletionState


# User schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    pii_data: Dict[str, Any] = Field(..., description="PII data to be encrypted")
    consent_purposes: List[str] = Field(default=[], description="Required consent purposes")


class UserUpdate(BaseModel):
    pii_data: Optional[Dict[str, Any]] = Field(None, description="Updated PII data")
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserWithPII(UserResponse):
    """Response that includes decrypted PII - use with caution"""
    pii_data: Dict[str, Any]


# Consent schemas
class ConsentBase(BaseModel):
    purpose: str = Field(..., description="Purpose for data processing")
    granted: bool = Field(..., description="Whether consent is granted")


class ConsentCreate(ConsentBase):
    user_id: int


class ConsentResponse(ConsentBase):
    id: int
    user_id: int
    timestamp: datetime
    
    model_config = {"from_attributes": True}


# Audit Log schemas
class AuditLogResponse(BaseModel):
    id: int
    actor: str
    action: str
    subject_type: str
    subject_id: int
    details_json: Optional[str]
    ts: datetime
    
    model_config = {"from_attributes": True}


# Deletion Request schemas
class DeletionRequestCreate(BaseModel):
    user_id: int


class DeletionRequestResponse(BaseModel):
    id: int
    user_id: int
    state: DeletionState
    requested_at: datetime
    processed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Export schemas
class UserExport(BaseModel):
    """Complete user data export for GDPR compliance"""
    user: UserResponse
    consents: List[ConsentResponse]
    pii_data: Dict[str, Any]


# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
