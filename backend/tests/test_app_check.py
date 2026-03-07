"""
Tests for Firebase App Check verification.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
from app.main import app

@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)

class TestAppCheck:
    """Test App Check implementation in API layers"""

    @patch("app.api.auth_bearer.verify_app_check_token")
    def test_app_check_missing_header_enforced(self, mock_verify, client):
        """Test that missing header fails when enforced"""
        # Mock verification to return False when enforced and header missing
        # (Though our implementation calls it with None which returns False if enforced)
        mock_verify.return_value = False
        
        response = client.get("/api/status")
        
        # Should be 401 Unauthorized because App Check failed
        assert response.status_code == 401
        assert "Unauthorized app traffic" in response.json()["detail"]
        mock_verify.assert_called_once_with(None)

    @patch("app.api.auth_bearer.verify_app_check_token")
    def test_app_check_valid_header_enforced(self, mock_verify, client):
        """Test that valid header passes even when enforced"""
        mock_verify.return_value = True
        
        # We still need JWT to pass the second layer of security in get_status
        # but let's see if it reaches that far. 
        # Actually, let's use a simpler endpoint if any? 
        # /api/health does NOT use JWTBearer.
        
        # Let's check which endpoints use JWTBearer. 
        # Almost all in routes.py use Depends(get_current_user_phone) which uses JWTBearer.
        
        response = client.get("/api/status", headers={"X-Firebase-AppCheck": "valid_token"})
        
        # Status code won't be 200 because JWT will fail next, 
        # but it shouldn't be 401 "Unauthorized app traffic".
        # It should be 403 "Not authenticated" or similar from HTTPBearer.
        assert response.status_code != 401 or response.json()["detail"] != "Unauthorized app traffic."
        mock_verify.assert_called_once_with("valid_token")

    @patch("app.api.auth_bearer.verify_app_check_token")
    def test_app_check_not_enforced(self, mock_verify, client):
        """Test that App Check passes when not enforced even if token invalid"""
        # In our implementation, verify_app_check_token returns True if ENFORCE_APP_CHECK=false
        mock_verify.return_value = True
        
        response = client.get("/api/status")
        
        # Should not be 401 "Unauthorized app traffic"
        if response.status_code == 401:
             assert response.json()["detail"] != "Unauthorized app traffic."

class TestAppCheckDomain:
    """Test the domain logic for App Check verification"""
    
    @patch("app.domain.auth_provider.app_check")
    @patch("app.domain.auth_provider.initialize_firebase")
    def test_verify_token_logic_enforced_valid(self, mock_init, mock_app_check, monkeypatch):
        """Test domain verification logic when enforced and valid"""
        from app.domain.auth_provider import verify_app_check_token
        
        monkeypatch.setenv("ENFORCE_APP_CHECK", "true")
        mock_init.return_value = True
        mock_app_check.verify_token.return_value = MagicMock() # Success
        
        result = verify_app_check_token("valid_token")
        assert result is True
        mock_app_check.verify_token.assert_called_once_with("valid_token")

    @patch("app.domain.auth_provider.app_check")
    @patch("app.domain.auth_provider.initialize_firebase")
    def test_verify_token_logic_enforced_invalid(self, mock_init, mock_app_check, monkeypatch):
        """Test domain verification logic when enforced and invalid"""
        from app.domain.auth_provider import verify_app_check_token
        
        monkeypatch.setenv("ENFORCE_APP_CHECK", "true")
        mock_init.return_value = True
        mock_app_check.verify_token.side_effect = Exception("Invalid token")
        
        result = verify_app_check_token("invalid_token")
        assert result is False

    @patch("app.domain.auth_provider.app_check")
    @patch("app.domain.auth_provider.initialize_firebase")
    def test_verify_token_logic_not_enforced_invalid(self, mock_init, mock_app_check, monkeypatch):
        """Test domain verification logic when NOT enforced and invalid"""
        from app.domain.auth_provider import verify_app_check_token
        
        monkeypatch.setenv("ENFORCE_APP_CHECK", "false")
        mock_init.return_value = True
        mock_app_check.verify_token.side_effect = Exception("Invalid token")
        
        result = verify_app_check_token("invalid_token")
        # Should be True because ENFORCE_APP_CHECK is false
        assert result is True
