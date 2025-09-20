"""
Audit logging utilities and decorators
"""
import json
from functools import wraps
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models import AuditLog
from app.deps import get_database


def audit_log(
    action: str,
    subject_type: str,
    actor: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    Decorator to automatically log actions to audit log
    
    Args:
        action: Action being performed (e.g., "create", "update", "delete")
        subject_type: Type of subject being acted upon (e.g., "user", "consent")
        actor: Actor performing the action (defaults to "system")
        details: Additional details to log
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract database session and other parameters
            db: Session = None
            subject_id: Optional[int] = None
            
            # Try to find db session in kwargs
            if 'db' in kwargs:
                db = kwargs['db']
            
            # Try to find subject_id in kwargs or return value
            if 'user_id' in kwargs:
                subject_id = kwargs['user_id']
            elif 'id' in kwargs:
                subject_id = kwargs['id']
            
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Log to audit log if we have the required info
            if db and subject_id:
                audit_entry = AuditLog(
                    actor=actor or "system",
                    action=action,
                    subject_type=subject_type,
                    subject_id=subject_id,
                    details_json=json.dumps(details) if details else None
                )
                db.add(audit_entry)
                db.commit()
            
            return result
        return wrapper
    return decorator


def log_audit_event(
    db: Session,
    actor: str,
    action: str,
    subject_type: str,
    subject_id: int,
    details: Optional[Dict[str, Any]] = None
):
    """Manually log an audit event"""
    audit_entry = AuditLog(
        actor=actor,
        action=action,
        subject_type=subject_type,
        subject_id=subject_id,
        details_json=json.dumps(details) if details else None
    )
    db.add(audit_entry)
    db.commit()
    return audit_entry
