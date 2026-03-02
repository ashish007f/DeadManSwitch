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
    auth_repo = AuthRepository(mock_db)
    auth_repo.get_or_create_user(phone)
    
    # Create JWT
    from app.domain.security import create_access_token
    access_token = create_access_token(data={"sub": phone})
    
    # Set the token on the client
    client.headers["Authorization"] = f"Bearer {access_token}"
    
    return phone, client

def test_rate_limit_general_status(authenticated_user):
    """Test that general endpoints are rate limited (default 10/minute)"""
    phone, client = authenticated_user
    
    # We should be able to make 10 requests
    for i in range(10):
        response = client.get("/api/status")
        assert response.status_code == 200, f"Request {i+1} failed"
    
    # The 11th request should be rate limited
    response = client.get("/api/status")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]

def test_rate_limit_auth_verify_firebase(client):
    """Test that auth endpoints are more strictly rate limited (default 5/minute)"""
    # We should be able to make 5 requests
    # Note: We don't need a valid token for rate limiting to trigger, 
    # as the limit is applied before the function logic.
    # However, to avoid 401s getting in the way, we check 5/minute.
    
    for i in range(5):
        # Even with invalid token, the limiter counts the attempt
        response = client.post("/api/auth/verify-firebase", json={"id_token": "some_token"})
        # It should be 401 (Unauthorized) or 400, but NOT 429
        assert response.status_code != 429, f"Request {i+1} was prematurely rate limited"
    
    # The 6th request should be rate limited
    response = client.post("/api/auth/verify-firebase", json={"id_token": "some_token"})
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]

def test_rate_limit_auth_refresh(client):
    """Test rate limiting on refresh token endpoint"""
    for i in range(5):
        response = client.post("/api/auth/refresh", json={"refresh_token": "some_token"})
        assert response.status_code != 429
        
    response = client.post("/api/auth/refresh", json={"refresh_token": "some_token"})
    assert response.status_code == 429

def test_rate_limit_reset_after_storage_clear(authenticated_user):
    """Verify that resetting storage allows requests again"""
    phone, client = authenticated_user
    
    # Trigger rate limit
    for _ in range(10):
        client.get("/api/status")
    assert client.get("/api/status").status_code == 429
    
    # Reset storage
    limiter._storage.reset()
    
    # Should work again
    assert client.get("/api/status").status_code == 200
