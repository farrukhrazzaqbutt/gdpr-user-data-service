"""
Test database models
"""
import pytest
from datetime import datetime
from app.models import User, Consent, AuditLog, DeletionRequest, DeletionState


class TestUserModel:
    def test_create_user(self, db_session):
        """Test creating a user"""
        user = User(
            email="test@example.com",
            pii_encrypted="encrypted_data_here"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.pii_encrypted == "encrypted_data_here"
        assert user.created_at is not None
    
    def test_user_relationships(self, db_session):
        """Test user relationships with consents and deletion requests"""
        user = User(
            email="test@example.com",
            pii_encrypted="encrypted_data_here"
        )
        db_session.add(user)
        db_session.flush()
        
        # Add consent
        consent = Consent(
            user_id=user.id,
            purpose="marketing",
            granted=True
        )
        db_session.add(consent)
        
        # Add deletion request
        deletion_request = DeletionRequest(
            user_id=user.id,
            state=DeletionState.PENDING
        )
        db_session.add(deletion_request)
        db_session.commit()
        
        # Test relationships
        assert len(user.consents) == 1
        assert user.consents[0].purpose == "marketing"
        assert len(user.deletion_requests) == 1
        assert user.deletion_requests[0].state == DeletionState.PENDING


class TestConsentModel:
    def test_create_consent(self, db_session):
        """Test creating a consent"""
        user = User(email="test@example.com")
        db_session.add(user)
        db_session.flush()
        
        consent = Consent(
            user_id=user.id,
            purpose="analytics",
            granted=False
        )
        db_session.add(consent)
        db_session.commit()
        
        assert consent.id is not None
        assert consent.user_id == user.id
        assert consent.purpose == "analytics"
        assert consent.granted is False
        assert consent.timestamp is not None


class TestAuditLogModel:
    def test_create_audit_log(self, db_session):
        """Test creating an audit log entry"""
        audit_log = AuditLog(
            actor="test_user",
            action="create",
            subject_type="user",
            subject_id=123,
            details_json='{"test": "data"}'
        )
        db_session.add(audit_log)
        db_session.commit()
        
        assert audit_log.id is not None
        assert audit_log.actor == "test_user"
        assert audit_log.action == "create"
        assert audit_log.subject_type == "user"
        assert audit_log.subject_id == 123
        assert audit_log.details_json == '{"test": "data"}'
        assert audit_log.ts is not None


class TestDeletionRequestModel:
    def test_create_deletion_request(self, db_session):
        """Test creating a deletion request"""
        user = User(email="test@example.com")
        db_session.add(user)
        db_session.flush()
        
        deletion_request = DeletionRequest(
            user_id=user.id,
            state=DeletionState.PENDING
        )
        db_session.add(deletion_request)
        db_session.commit()
        
        assert deletion_request.id is not None
        assert deletion_request.user_id == user.id
        assert deletion_request.state == DeletionState.PENDING
        assert deletion_request.requested_at is not None
        assert deletion_request.processed_at is None
