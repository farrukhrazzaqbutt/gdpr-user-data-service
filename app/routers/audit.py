"""
Audit log endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import get_admin_user
from app.schemas import AuditLogResponse
from app.models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    subject_type: Optional[str] = Query(None, description="Filter by subject type"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    offset: int = Query(0, description="Number of logs to skip"),
    db: Session = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    """Get audit logs (admin only)"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.subject_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if subject_type:
        query = query.filter(AuditLog.subject_type == subject_type)
    
    logs = query.order_by(AuditLog.ts.desc()).offset(offset).limit(limit).all()
    return [AuditLogResponse.from_orm(log) for log in logs]
