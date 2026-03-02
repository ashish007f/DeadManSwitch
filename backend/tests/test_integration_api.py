"""
Integration tests for API endpoints using Mock Firestore.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from mockfirestore import MockFirestore
from app.main import app
from app.db.database import get_db


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Create a fresh mock firestore for each test"""
    mock_db = MockFirestore()
    
    # Override the app's database dependency
    def override_get_db():
        yield mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield mock_db
    
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def authenticated_user(client, setup_test_db):
    """Create and authenticate a test user (JWT Injection)"""
    phone = "+16502530000"
    mock_db = setup_test_db
    
    # Ensure user exists in the mock DB
    from app.repositories.auth_repo import AuthRepository
    from app.domain.security import secure_phone_identity
    auth_repo = AuthRepository(mock_db)
    user = auth_repo.get_or_create_user_by_phone(phone)
    
    # Create JWT using the hash as 'sub'
    from app.domain.security import create_access_token
    access_token = create_access_token(data={"sub": user.phone_hash})
    
    # Set the token on the client
    client.headers["Authorization"] = f"Bearer {access_token}"
    
    return phone, client


class TestProductionAuthentication:
    """Test production-ready authentication flows"""
    
    def test_verify_firebase_invalid_token(self, client):
        """Test Firebase verification with bad token"""
        response = client.post("/api/auth/verify-firebase", json={"id_token": "fake_token"})
        assert response.status_code == 401
        assert "invalid or expired Firebase token" in response.json()["detail"]

    def test_logout(self, authenticated_user):
        """Test logout clears header (Simulation)"""
        phone, client = authenticated_user
        
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        
        # Client side would clear header
        del client.headers["Authorization"]
        
        # Verify unauthorized
        response = client.get("/api/status")
        assert response.status_code == 401


class TestCheckIn:
    """Test check-in functionality"""
    
    def test_record_checkin_authenticated(self, authenticated_user):
        """Test recording check-in when authenticated"""
        phone, client = authenticated_user
        
        response = client.post("/api/checkin", json={})
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "status" in data
        assert "hours_until_due" in data
        assert data["status"] in ["SAFE", "DUE_SOON", "MISSED", "GRACE_PERIOD", "NOTIFIED"]
    
    def test_record_checkin_unauthenticated(self, client):
        """Test recording check-in without authentication"""
        response = client.post("/api/checkin", json={})
        assert response.status_code == 401
    
    def test_get_status_authenticated(self, authenticated_user):
        """Test getting status when authenticated"""
        phone, client = authenticated_user
        
        # Record a check-in first
        client.post("/api/checkin", json={})
        
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "last_checkin" in data
        assert "hours_until_due" in data
        assert "interval_hours" in data
    
    def test_get_status_unauthenticated(self, client):
        """Test getting status without authentication"""
        response = client.get("/api/status")
        assert response.status_code == 401


class TestSettings:
    """Test settings management"""
    
    def test_get_settings_defaults(self, authenticated_user):
        """Test getting default settings"""
        phone, client = authenticated_user
        
        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["checkin_interval_hours"] == 48.0
        assert data["missed_buffer_hours"] == 1.0
        assert data["grace_period_hours"] == 24.0
    
    def test_update_settings(self, authenticated_user):
        """Test updating settings"""
        phone, client = authenticated_user
        
        update_data = {
            "checkin_interval_hours": 24.0,
            "missed_buffer_hours": 2.0,
            "grace_period_hours": 48.0,
            "contacts": ["alice@example.com", "bob@example.com"]
        }
        
        response = client.post("/api/settings", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["checkin_interval_hours"] == 24.0
        assert data["missed_buffer_hours"] == 2.0
        assert data["grace_period_hours"] == 48.0
        assert len(data["contacts"]) == 2
    
    def test_update_settings_partial(self, authenticated_user):
        """Test updating only some settings"""
        phone, client = authenticated_user
        
        # Update only interval
        response = client.post("/api/settings", json={"checkin_interval_hours": 72.0})
        assert response.status_code == 200
        data = response.json()
        assert data["checkin_interval_hours"] == 72.0
        # Other fields should remain default (fetched from Firestore update)
        assert data["missed_buffer_hours"] == 1.0


class TestInstructions:
    """Test instructions management"""
    
    def test_save_instructions(self, authenticated_user):
        """Test saving instructions"""
        phone, client = authenticated_user
        
        instructions = "Bank account: 123456789\nInvestment advisor: John Doe\n"
        response = client.post("/api/instructions", json={"content": instructions})
        assert response.status_code == 200
        assert response.json()["content"] == instructions
    
    def test_get_instructions(self, authenticated_user):
        """Test getting instructions"""
        phone, client = authenticated_user
        
        # Save first
        instructions = "Emergency contact: 555-999-8888"
        client.post("/api/instructions", json={"content": instructions})
        
        # Get
        response = client.get("/api/instructions")
        assert response.status_code == 200
        assert response.json()["content"] == instructions
    
    def test_instructions_empty(self, authenticated_user):
        """Test getting instructions when none exist"""
        phone, client = authenticated_user
        
        response = client.get("/api/instructions")
        assert response.status_code == 200
        assert response.json()["content"] is None or response.json()["content"] == ""


class TestUserFlow:
    """Test complete user workflows"""
    
    def test_full_user_flow(self, client, setup_test_db):
        """Test complete flow: login → check-in → status → settings"""
        phone = "+12125550000"
        mock_db = setup_test_db
        
        # 1. Ensure user exists in the mock DB
        from app.repositories.auth_repo import AuthRepository
        from app.domain.security import secure_phone_identity
        user = AuthRepository(mock_db).get_or_create_user_by_phone(phone)

        # 2. Authenticate using hash
        from app.domain.security import create_access_token
        access_token = create_access_token(data={"sub": user.phone_hash})
        client.headers["Authorization"] = f"Bearer {access_token}"
        
        # 3. Check-in
        response = client.post("/api/checkin", json={})
        assert response.status_code == 200
        assert response.json()["status"] == "SAFE"
        
        # 4. Get status
        response = client.get("/api/status")
        assert response.status_code == 200
        assert response.json()["status"] == "SAFE"
        
        # 5. Update settings
        response = client.post("/api/settings", json={"checkin_interval_hours": 1.0})
        assert response.status_code == 200
        
        # 6. Save instructions
        response = client.post("/api/instructions", json={"content": "Test instructions"})
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_endpoint(self, client):
        """Test 404 for invalid endpoint"""
        response = client.get("/api/invalid")
        assert response.status_code == 404
    
        def test_me_endpoint_authenticated(self, authenticated_user):
            """Test /me endpoint when authenticated"""
            phone, client = authenticated_user
            from app.domain.security import secure_phone_identity
            _, p_hash = secure_phone_identity(phone)
        
            response = client.get("/api/me")
            assert response.status_code == 200
            assert response.json()["phone"] == p_hash    
    def test_me_endpoint_unauthenticated(self, client):
        """Test /me endpoint when not authenticated"""
        response = client.get("/api/me")
        assert response.status_code == 401
