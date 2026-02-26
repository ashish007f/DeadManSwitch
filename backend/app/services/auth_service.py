"""
Authentication service layer.

Orchestrates authentication workflows (Firebase verification, profile management).
Handles authentication business logic.
"""

from sqlalchemy.orm import Session
from app.repositories.auth_repo import AuthRepository
from app.domain.auth_provider import verify_firebase_token
from app.domain.security import create_access_token, create_refresh_token, decode_token
from datetime import datetime


class AuthService:
    """Orchestrate authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_repo = AuthRepository(db)
    
    def verify_firebase_login(self, id_token: str) -> dict | None:
        """
        Exchange a Firebase ID token for a local user and issue JWTs.
        """
        claims = verify_firebase_token(id_token)
        if not claims:
            return None
            
        phone = claims.get("phone_number")
        if not phone:
            return None
            
        user = self.auth_repo.get_or_create_user(phone)
        user.verified = 1
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Issue JWTs
        access_token = create_access_token(data={"sub": user.phone_number})
        refresh_token = create_refresh_token(data={"sub": user.phone_number})
        
        return {
            "phone": user.phone_number,
            "display_name": user.display_name,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    def refresh_access_token(self, refresh_token: str) -> dict | None:
        """Issue a new access token from a valid refresh token"""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
            
        phone = payload.get("sub")
        if not phone:
            return None
            
        # Optional: check if user still exists/is active
        
        new_access_token = create_access_token(data={"sub": phone})
        return {"access_token": new_access_token}

    def update_display_name(self, phone: str, display_name: str) -> dict:
        """
        Update user's display name (optional profile setup).
        
        Returns:
            Dict with updated user info
        """
        user = self.auth_repo.update_display_name(phone, display_name)
        return {
            "phone": user.phone_number,
            "display_name": user.display_name
        }

    def get_user_info(self, phone: str) -> dict | None:
        """
        Get user information by phone.
        
        Returns:
            Dict with user info or None if user doesn't exist
        """
        user = self.auth_repo.get_user_by_phone(phone)
        if not user:
            return None
        return {
            "phone": user.phone_number,
            "display_name": user.display_name,
            "verified": bool(user.verified)
        }
