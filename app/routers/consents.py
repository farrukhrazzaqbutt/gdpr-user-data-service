"""
Consent management endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import get_current_user
from app.schemas import ConsentCreate, ConsentResponse
from app.services.consent_service import ConsentService

router = APIRouter(prefix="/consents", tags=["consents"])


@router.post("/", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def create_consent(
    consent_data: ConsentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new consent record"""
    consent_service = ConsentService(db)
    return consent_service.create_consent(consent_data, current_user["username"])


@router.get("/", response_model=List[ConsentResponse])
async def get_consents(
    user_id: int = Query(..., description="User ID to get consents for"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all consents for a user"""
    consent_service = ConsentService(db)
    consents = consent_service.get_user_consents(user_id)
    return [ConsentResponse.from_orm(consent) for consent in consents]


@router.get("/{consent_id}", response_model=ConsentResponse)
async def get_consent(
    consent_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get consent by ID"""
    consent_service = ConsentService(db)
    consent = consent_service.get_consent(consent_id)
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found"
        )
    return ConsentResponse.from_orm(consent)


@router.patch("/{consent_id}", response_model=ConsentResponse)
async def update_consent(
    consent_id: int,
    granted: bool,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update consent status"""
    consent_service = ConsentService(db)
    try:
        return consent_service.update_consent(consent_id, granted, current_user["username"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found"
        )
