"""
Consent management service
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Consent
from app.schemas import ConsentCreate, ConsentResponse
from app.utils.audit import log_audit_event


class ConsentService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_consent(self, consent_data: ConsentCreate, actor: str = "system") -> Consent:
        """Create a new consent record"""
        consent = Consent(
            user_id=consent_data.user_id,
            purpose=consent_data.purpose,
            granted=consent_data.granted
        )
        self.db.add(consent)
        self.db.commit()
        
        # Log audit event
        log_audit_event(
            self.db, actor, "create", "consent", consent.id,
            {"user_id": consent_data.user_id, "purpose": consent_data.purpose, "granted": consent_data.granted}
        )
        
        return consent
    
    def get_user_consents(self, user_id: int) -> List[Consent]:
        """Get all consents for a user"""
        return self.db.query(Consent).filter(Consent.user_id == user_id).all()
    
    def get_consent(self, consent_id: int) -> Optional[Consent]:
        """Get consent by ID"""
        return self.db.query(Consent).filter(Consent.id == consent_id).first()
    
    def update_consent(self, consent_id: int, granted: bool, actor: str = "system") -> Consent:
        """Update consent status"""
        consent = self.get_consent(consent_id)
        if not consent:
            raise ValueError("Consent not found")
        
        old_status = consent.granted
        consent.granted = granted
        self.db.commit()
        
        # Log audit event
        log_audit_event(
            self.db, actor, "update", "consent", consent_id,
            {"user_id": consent.user_id, "purpose": consent.purpose, "old_granted": old_status, "new_granted": granted}
        )
        
        return consent
    
    def get_consent_by_user_and_purpose(self, user_id: int, purpose: str) -> Optional[Consent]:
        """Get consent by user ID and purpose"""
        return self.db.query(Consent).filter(
            Consent.user_id == user_id,
            Consent.purpose == purpose
        ).first()
    
    def revoke_all_consents(self, user_id: int, actor: str = "system") -> int:
        """Revoke all consents for a user (used in RTBF)"""
        updated_count = self.db.query(Consent).filter(
            Consent.user_id == user_id,
            Consent.granted == True
        ).update({"granted": False})
        
        self.db.commit()
        
        # Log audit event
        log_audit_event(
            self.db, actor, "revoke_all", "consent", user_id,
            {"revoked_count": updated_count}
        )
        
        return updated_count
