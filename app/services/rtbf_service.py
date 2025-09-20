"""
Right-to-be-Forgotten (RTBF) service
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import DeletionRequest, DeletionState, User, Consent
from app.schemas import DeletionRequestCreate, DeletionRequestResponse
from app.utils.audit import log_audit_event
from app.crypto import encrypt_pii
import secrets
import string


class RTBFService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_deletion_request(self, request_data: DeletionRequestCreate, actor: str = "system") -> DeletionRequest:
        """Create a new deletion request"""
        # Check if there's already a pending request
        existing = self.db.query(DeletionRequest).filter(
            DeletionRequest.user_id == request_data.user_id,
            DeletionRequest.state == DeletionState.PENDING
        ).first()
        
        if existing:
            return existing
        
        deletion_request = DeletionRequest(
            user_id=request_data.user_id,
            state=DeletionState.PENDING
        )
        self.db.add(deletion_request)
        self.db.commit()
        
        # Log audit event
        log_audit_event(
            self.db, actor, "create_rtbf", "deletion_request", deletion_request.id,
            {"user_id": request_data.user_id}
        )
        
        return deletion_request
    
    def get_deletion_request(self, request_id: int) -> Optional[DeletionRequest]:
        """Get deletion request by ID"""
        return self.db.query(DeletionRequest).filter(DeletionRequest.id == request_id).first()
    
    def get_pending_requests(self) -> List[DeletionRequest]:
        """Get all pending deletion requests"""
        return self.db.query(DeletionRequest).filter(
            DeletionRequest.state == DeletionState.PENDING
        ).all()
    
    def process_deletion_request(self, request_id: int, actor: str = "system") -> bool:
        """Process a deletion request (anonymize data)"""
        deletion_request = self.get_deletion_request(request_id)
        if not deletion_request:
            return False
        
        if deletion_request.state != DeletionState.PENDING:
            return False  # Already processed or failed
        
        try:
            # Update state to processing
            deletion_request.state = DeletionState.PROCESSING
            self.db.commit()
            
            # Get user
            user = self.db.query(User).filter(User.id == deletion_request.user_id).first()
            if not user:
                deletion_request.state = DeletionState.FAILED
                self.db.commit()
                return False
            
            # Anonymize PII data
            anonymized_pii = self._generate_anonymized_pii()
            encrypted_pii = encrypt_pii(anonymized_pii)
            user.pii_encrypted = encrypted_pii.hex()
            
            # Revoke all consents
            self.db.query(Consent).filter(
                Consent.user_id == deletion_request.user_id,
                Consent.granted == True
            ).update({"granted": False})
            
            # Mark as completed
            deletion_request.state = DeletionState.COMPLETED
            deletion_request.processed_at = datetime.utcnow()
            self.db.commit()
            
            # Log audit event
            log_audit_event(
                self.db, actor, "process_rtbf", "deletion_request", request_id,
                {"user_id": deletion_request.user_id, "action": "anonymized_pii_and_revoked_consents"}
            )
            
            return True
            
        except Exception as e:
            # Mark as failed
            deletion_request.state = DeletionState.FAILED
            self.db.commit()
            
            # Log error
            log_audit_event(
                self.db, actor, "rtbf_error", "deletion_request", request_id,
                {"user_id": deletion_request.user_id, "error": str(e)}
            )
            
            return False
    
    def _generate_anonymized_pii(self) -> dict:
        """Generate anonymized PII data that cannot be recovered"""
        # Generate random tokens that look like real data but are completely random
        def random_string(length: int) -> str:
            return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
        
        return {
            "name": f"ANONYMIZED_{random_string(8)}",
            "phone": f"+{random_string(10)}",
            "address": f"ANONYMIZED_ADDRESS_{random_string(12)}",
            "anonymized_at": "2024-01-01T00:00:00Z",
            "note": "This data has been anonymized and cannot be recovered"
        }
    
    def is_rtbf_safe(self, user_id: int) -> bool:
        """Check if user data is safe for RTBF (no pending requests)"""
        pending = self.db.query(DeletionRequest).filter(
            DeletionRequest.user_id == user_id,
            DeletionRequest.state == DeletionState.PENDING
        ).first()
        return pending is None
