"""
Integration tests for API endpoints.

Tests full request/response cycle including authentication, check-ins, settings, and notifications.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.schema import Base, User, Settings, CheckIn, Instructions
from app.db.database import get_db
from sqlalchemy.pool import StaticPool 


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Create a fresh in-memory database for each test"""
    # Create new in-memory database
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool )
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Override the app's database dependency
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()
    # print(f"\n[DEBUG] Tables in Memory: {Base.metadata.tables.keys()}")


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def authenticated_user(client):
    """Create and authenticate a test user (JWT Injection)"""
    phone = "+16502530000"
    
    # Ensure user exists in the DB
    from app.db.database import get_db
    db = next(app.dependency_overrides[get_db]())
    try:
        from app.repositories.auth_repo import AuthRepository
        auth_repo = AuthRepository(db)
        auth_repo.get_or_create_user(phone)
    finally:
        db.close()
    
    # Create JWT
    from app.domain.security import create_access_token
    access_token = create_access_token(data={"sub": phone})
    
    # Set the token on the client for all subsequent requests in this session
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
        assert response.status_code == 401 # HTTPBearer returns 401 for missing header


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
        assert data["checkin_interval_hours"] == 48
        assert data["missed_buffer_hours"] == 1
        assert data["grace_period_hours"] == 24
    
    def test_update_settings(self, authenticated_user):
        """Test updating settings"""
        phone, client = authenticated_user
        
        update_data = {
            "checkin_interval_hours": 24,
            "missed_buffer_hours": 2,
            "grace_period_hours": 48,
            "contacts": ["alice@example.com", "bob@example.com"]
        }
        
        response = client.post("/api/settings", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["checkin_interval_hours"] == 24
        assert data["missed_buffer_hours"] == 2
        assert data["grace_period_hours"] == 48
        assert len(data["contacts"]) == 2
    
    def test_update_settings_partial(self, authenticated_user):
        """Test updating only some settings"""
        phone, client = authenticated_user
        
        # Update only interval
        response = client.post("/api/settings", json={"checkin_interval_hours": 72})
        assert response.status_code == 200
        data = response.json()
        assert data["checkin_interval_hours"] == 72
        # Other fields should remain default
        assert data["missed_buffer_hours"] == 1


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
    
    def test_full_user_flow(self, client):
        """Test complete flow: login → check-in → status → settings"""
        phone = "+12125550000"
        
        # 1. Login (Simulate JWT)
        from app.domain.security import create_access_token
        access_token = create_access_token(data={"sub": phone})
        client.headers["Authorization"] = f"Bearer {access_token}"
        
        # Ensure user exists in the correct DB
        from app.db.database import get_db
        db = next(app.dependency_overrides[get_db]())
        try:
            from app.repositories.auth_repo import AuthRepository
            AuthRepository(db).get_or_create_user(phone)
        finally:
            db.close()
        
        # 2. Check-in
        response = client.post("/api/checkin", json={})
        assert response.status_code == 200
        assert response.json()["status"] == "SAFE"
        
        # 3. Get status
        response = client.get("/api/status")
        assert response.status_code == 200
        assert response.json()["status"] == "SAFE"
        
        # 4. Update settings
        response = client.post("/api/settings", json={"checkin_interval_hours": 1})
        assert response.status_code == 200
        
        # 5. Save instructions
        response = client.post("/api/instructions", json={"content": "Test instructions"})
        assert response.status_code == 200
    
    def test_checkin_upsert_behavior(self, authenticated_user):
        """Test that check-ins upsert (only one row per user)"""
        phone, client = authenticated_user
        
        # Record first check-in
        response1 = client.post("/api/checkin", json={})
        timestamp1 = response1.json()["timestamp"]
        
        # Record second check-in
        response2 = client.post("/api/checkin", json={})
        timestamp2 = response2.json()["timestamp"]
        
        # Second timestamp should be newer
        assert timestamp2 > timestamp1
        
        # Status should reflect latest check-in
        response = client.get("/api/status")
        assert response.status_code == 200
        assert response.json()["last_checkin"] == timestamp2


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_endpoint(self, client):
        """Test 404 for invalid endpoint"""
        response = client.get("/api/invalid")
        assert response.status_code == 404
    
    def test_me_endpoint_authenticated(self, authenticated_user):
        """Test /me endpoint when authenticated"""
        phone, client = authenticated_user
        
        response = client.get("/api/me")
        assert response.status_code == 200
        assert response.json()["phone"] == phone
    
    def test_me_endpoint_unauthenticated(self, client):
        """Test /me endpoint when not authenticated"""
        response = client.get("/api/me")
        assert response.status_code == 401
