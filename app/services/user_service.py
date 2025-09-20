"""
User service with PII encryption/decryption
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models import User, Consent
from app.schemas import UserCreate, UserUpdate, UserWithPII
from app.crypto import encrypt_pii, decrypt_pii
from app.utils.audit import log_audit_event


class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate, actor: str = "system") -> User:
        """Create a new user with encrypted PII"""
        try:
            # Encrypt PII data
            encrypted_pii = encrypt_pii(user_data.pii_data)
            
            # Create user
            user = User(
                email=user_data.email,
                pii_encrypted=encrypted_pii.hex()  # Store as hex string
            )
            self.db.add(user)
            self.db.flush()  # Get the ID
            
            # Create consents
            for purpose in user_data.consent_purposes:
                consent = Consent(
                    user_id=user.id,
                    purpose=purpose,
                    granted=True  # Assume granted for creation
                )
                self.db.add(consent)
            
            self.db.commit()
            
            # Log audit event
            log_audit_event(
                self.db, actor, "create", "user", user.id,
                {"email": user.email, "consent_purposes": user_data.consent_purposes}
            )
            
            return user
            
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    def get_user(self, user_id: int, include_pii: bool = False) -> User:
        """Get user by ID, optionally with decrypted PII"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    def get_user_with_pii(self, user_id: int) -> UserWithPII:
        """Get user with decrypted PII data"""
        user = self.get_user(user_id)
        
        # Decrypt PII
        pii_data = {}
        if user.pii_encrypted:
            try:
                encrypted_bytes = bytes.fromhex(user.pii_encrypted)
                pii_data = decrypt_pii(encrypted_bytes)
            except Exception as e:
                # Log error but don't expose it
                log_audit_event(
                    self.db, "system", "decrypt_error", "user", user_id,
                    {"error": "Failed to decrypt PII data"}
                )
                pii_data = {"error": "Unable to decrypt PII data"}
        
        return UserWithPII(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            pii_data=pii_data
        )
    
    def update_user(self, user_id: int, user_update: UserUpdate, actor: str = "system") -> User:
        """Update user data, re-encrypting PII if changed"""
        user = self.get_user(user_id)
        
        # Update email if provided
        if user_update.email:
            user.email = user_update.email
        
        # Update PII if provided
        if user_update.pii_data:
            encrypted_pii = encrypt_pii(user_update.pii_data)
            user.pii_encrypted = encrypted_pii.hex()
        
        self.db.commit()
        
        # Log audit event
        log_audit_event(
            self.db, actor, "update", "user", user_id,
            {"updated_fields": list(user_update.dict(exclude_unset=True).keys())}
        )
        
        return user
    
    def delete_user(self, user_id: int, actor: str = "system") -> bool:
        """Soft delete user (anonymize PII)"""
        user = self.get_user(user_id)
        
        # Anonymize PII data
        anonymized_pii = {
            "name": f"User_{user_id}",
            "phone": "REDACTED",
            "address": "REDACTED"
        }
        encrypted_pii = encrypt_pii(anonymized_pii)
        user.pii_encrypted = encrypted_pii.hex()
        
        # Revoke all consents
        self.db.query(Consent).filter(Consent.user_id == user_id).update({"granted": False})
        
        self.db.commit()
        
        # Log audit event
        log_audit_event(
            self.db, actor, "delete", "user", user_id,
            {"action": "anonymized_pii", "consents_revoked": True}
        )
        
        return True
    
    def check_consent(self, user_id: int, purpose: str) -> bool:
        """Check if user has granted consent for a specific purpose"""
        consent = self.db.query(Consent).filter(
            Consent.user_id == user_id,
            Consent.purpose == purpose,
            Consent.granted == True
        ).first()
        return consent is not None
    
    def get_user_consents(self, user_id: int) -> List[Consent]:
        """Get all consents for a user"""
        return self.db.query(Consent).filter(Consent.user_id == user_id).all()
    
    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """Export complete user data for GDPR compliance"""
        user = self.get_user(user_id)
        consents = self.get_user_consents(user_id)
        
        # Decrypt PII
        pii_data = {}
        if user.pii_encrypted:
            try:
                encrypted_bytes = bytes.fromhex(user.pii_encrypted)
                pii_data = decrypt_pii(encrypted_bytes)
            except Exception:
                pii_data = {"error": "Unable to decrypt PII data"}
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            },
            "consents": [
                {
                    "id": consent.id,
                    "purpose": consent.purpose,
                    "granted": consent.granted,
                    "timestamp": consent.timestamp.isoformat()
                }
                for consent in consents
            ],
            "pii_data": pii_data
        }
