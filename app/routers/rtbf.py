"""
Right-to-be-Forgotten (RTBF) endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import get_current_user, get_admin_user
from app.schemas import DeletionRequestCreate, DeletionRequestResponse
from app.services.rtbf_service import RTBFService

router = APIRouter(prefix="/rtbf", tags=["rtbf"])


@router.post("/", response_model=DeletionRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_deletion_request(
    request_data: DeletionRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new deletion request"""
    rtbf_service = RTBFService(db)
    return rtbf_service.create_deletion_request(request_data, current_user["username"])


@router.get("/{request_id}", response_model=DeletionRequestResponse)
async def get_deletion_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get deletion request by ID"""
    rtbf_service = RTBFService(db)
    request = rtbf_service.get_deletion_request(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deletion request not found"
        )
    return DeletionRequestResponse.from_orm(request)


@router.get("/", response_model=List[DeletionRequestResponse])
async def get_deletion_requests(
    user_id: int = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get deletion requests (admin only)"""
    rtbf_service = RTBFService(db)
    if user_id:
        # Get requests for specific user
        requests = [rtbf_service.get_deletion_request(r.id) for r in rtbf_service.get_pending_requests() 
                   if r.user_id == user_id]
        requests = [r for r in requests if r is not None]
    else:
        # Get all pending requests
        requests = rtbf_service.get_pending_requests()
    
    return [DeletionRequestResponse.from_orm(request) for request in requests]


@router.post("/{request_id}/process", response_model=DeletionRequestResponse)
async def process_deletion_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Process a deletion request (admin only)"""
    rtbf_service = RTBFService(db)
    success = rtbf_service.process_deletion_request(request_id, admin_user["username"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process deletion request"
        )
    
    request = rtbf_service.get_deletion_request(request_id)
    return DeletionRequestResponse.from_orm(request)
