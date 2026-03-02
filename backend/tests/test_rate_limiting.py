"""
Tests for Rate Limiting functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.config import settings
from app.limiter import limiter
from app.db.database import get_db
from mockfirestore import MockFirestore

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Create a fresh mock firestore and reset limiter for each test"""
    mock_db = MockFirestore()
    
    # Override the app's database dependency
    def override_get_db():
        yield mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Reset limiter storage
    limiter._storage.reset()
    
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
    
    # Create JWT using hash as 'sub'
    from app.domain.security import create_access_token
    access_token = create_access_token(data={"sub": user.phone_hash})
    
    # Set the token on the client
    client.headers["Authorization"] = f"Bearer {access_token}"
    
    return phone, client

def test_rate_limit_general_status(authenticated_user):
    """Test that general endpoints are rate limited (default 5/hour)"""
    phone, client = authenticated_user
    
    # We should be able to make 5 requests
    for i in range(5):
        response = client.get("/api/status")
        assert response.status_code == 200, f"Request {i+1} failed"
    
    # The 6th request should be rate limited
    response = client.get("/api/status")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]

def test_rate_limit_auth_verify_firebase(client):
    """Test that auth endpoints are more strictly rate limited (default 3/hour)"""
    for i in range(3):
        response = client.post("/api/auth/verify-firebase", json={"id_token": "some_token"})
        assert response.status_code != 429, f"Request {i+1} was prematurely rate limited"
    
    # The 4th request should be rate limited
    response = client.post("/api/auth/verify-firebase", json={"id_token": "some_token"})
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]

def test_rate_limit_auth_refresh(client):
    """Test rate limiting on refresh token endpoint"""
    for i in range(3):
        response = client.post("/api/auth/refresh", json={"refresh_token": "some_token"})
        assert response.status_code != 429
        
    response = client.post("/api/auth/refresh", json={"refresh_token": "some_token"})
    assert response.status_code == 429

def test_rate_limit_reset_after_storage_clear(authenticated_user):
    """Verify that resetting storage allows requests again"""
    phone, client = authenticated_user
    
    # Trigger rate limit
    for _ in range(5):
        client.get("/api/status")
    assert client.get("/api/status").status_code == 429
    
    # Reset storage
    limiter._storage.reset()
    
    # Should work again
    assert client.get("/api/status").status_code == 200
