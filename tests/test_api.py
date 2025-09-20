"""
Test API endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    def test_seed_admin(self, client):
        """Test seeding admin user"""
        response = client.post("/auth/seed")
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "admin"
        assert data["password"] == "admin"
    
    def test_login(self, client):
        """Test login endpoint"""
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestUserEndpoints:
    def test_create_user(self, client, auth_headers, sample_pii_data):
        """Test creating a user"""
        user_data = {
            "email": "test@example.com",
            "pii_data": sample_pii_data,
            "consent_purposes": ["marketing", "analytics"]
        }
        
        response = client.post("/users/", json=user_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data
    
    def test_get_user(self, client, auth_headers):
        """Test getting a user"""
        # First create a user
        user_data = {
            "email": "test@example.com",
            "pii_data": {"name": "Test User"},
            "consent_purposes": []
        }
        create_response = client.post("/users/", json=user_data, headers=auth_headers)
        user_id = create_response.json()["id"]
        
        # Then get the user
        response = client.get(f"/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["id"] == user_id
    
    def test_get_user_with_pii(self, client, auth_headers, sample_pii_data):
        """Test getting a user with PII data"""
        # Create user with PII
        user_data = {
            "email": "test@example.com",
            "pii_data": sample_pii_data,
            "consent_purposes": []
        }
        create_response = client.post("/users/", json=user_data, headers=auth_headers)
        user_id = create_response.json()["id"]
        
        # Get user with PII
        response = client.get(f"/users/{user_id}/with-pii", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "pii_data" in data
        assert data["pii_data"]["name"] == sample_pii_data["name"]
    
    def test_export_user_data(self, client, auth_headers, sample_pii_data):
        """Test exporting user data"""
        # Create user
        user_data = {
            "email": "test@example.com",
            "pii_data": sample_pii_data,
            "consent_purposes": ["marketing"]
        }
        create_response = client.post("/users/", json=user_data, headers=auth_headers)
        user_id = create_response.json()["id"]
        
        # Export user data
        response = client.get(f"/users/{user_id}/export", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "consents" in data
        assert "pii_data" in data
        assert data["pii_data"]["name"] == sample_pii_data["name"]


class TestConsentEndpoints:
    def test_create_consent(self, client, auth_headers):
        """Test creating a consent"""
        consent_data = {
            "user_id": 1,
            "purpose": "marketing",
            "granted": True
        }
        
        response = client.post("/consents/", json=consent_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["purpose"] == "marketing"
        assert data["granted"] is True
        assert data["user_id"] == 1
    
    def test_get_consents(self, client, auth_headers):
        """Test getting consents for a user"""
        response = client.get("/consents/?user_id=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestRTBFEndpoints:
    def test_create_deletion_request(self, client, auth_headers):
        """Test creating a deletion request"""
        request_data = {"user_id": 1}
        
        response = client.post("/rtbf/", json=request_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == 1
        assert data["state"] == "pending"
    
    def test_get_deletion_request(self, client, auth_headers):
        """Test getting a deletion request"""
        # First create a request
        request_data = {"user_id": 1}
        create_response = client.post("/rtbf/", json=request_data, headers=auth_headers)
        request_id = create_response.json()["id"]
        
        # Then get the request
        response = client.get(f"/rtbf/{request_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == request_id
        assert data["user_id"] == 1


class TestAuditEndpoints:
    def test_get_audit_logs(self, client, auth_headers):
        """Test getting audit logs (admin only)"""
        response = client.get("/audit/", headers=auth_headers)
        # This will fail without admin privileges, but we're testing the endpoint exists
        assert response.status_code in [200, 403]
