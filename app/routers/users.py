"""
User management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import get_current_user
from app.schemas import UserCreate, UserResponse, UserUpdate, UserWithPII, UserExport
from app.services.user_service import UserService
from app.services.consent_service import ConsentService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user with encrypted PII"""
    user_service = UserService(db)
    consent_service = ConsentService(db)
    
    # Check if required consents are granted
    for purpose in user_data.consent_purposes:
        if not consent_service.get_consent_by_user_and_purpose(current_user["user_id"], purpose):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Consent required for purpose: {purpose}"
            )
    
    return user_service.create_user(user_data, current_user["username"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user by ID (without PII)"""
    user_service = UserService(db)
    return user_service.get_user(user_id)


@router.get("/{user_id}/with-pii", response_model=UserWithPII)
async def get_user_with_pii(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user with decrypted PII (requires authorization)"""
    # In a real implementation, you'd check if current_user has permission
    # to view PII for this specific user
    user_service = UserService(db)
    return user_service.get_user_with_pii(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update user data"""
    user_service = UserService(db)
    return user_service.update_user(user_id, user_update, current_user["username"])


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Anonymize user data (soft delete)"""
    user_service = UserService(db)
    user_service.delete_user(user_id, current_user["username"])


@router.get("/{user_id}/export", response_model=UserExport)
async def export_user_data(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Export complete user data for GDPR compliance"""
    user_service = UserService(db)
    export_data = user_service.export_user_data(user_id)
    
    return UserExport(
        user=UserResponse.from_orm(user_service.get_user(user_id)),
        consents=[ConsentResponse.from_orm(c) for c in user_service.get_user_consents(user_id)],
        pii_data=export_data["pii_data"]
    )
