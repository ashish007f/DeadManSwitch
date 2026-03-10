"""
Authentication service layer.

Orchestrates authentication workflows (Firebase verification, profile management).
Handles authentication business logic.
"""

from google.cloud import firestore
from app.repositories.auth_repo import AuthRepository
from app.domain.auth_provider import verify_firebase_token
from app.domain.security import create_access_token, create_refresh_token, decode_token
from app.domain.encryption import decrypt_data
from datetime import datetime


class AuthService:
    """Orchestrate authentication operations"""
    
    def __init__(self, db: firestore.Client):
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
            
        user = self.auth_repo.get_or_create_user_by_phone(phone)
        self.auth_repo.update_last_login_by_phone(phone)
        
        # Issue JWTs - Use phone_hash as the 'sub' claim for privacy
        access_token = create_access_token(data={"sub": user.phone_hash})
        refresh_token = create_refresh_token(data={"sub": user.phone_hash})
        
        raw_phone = decrypt_data(user.encrypted_phone) if hasattr(user, "encrypted_phone") else phone

        return {
            "phone": user.phone_hash, 
            "raw_phone": raw_phone,
            "display_name": user.display_name,
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    def refresh_access_token(self, refresh_token: str) -> dict | None:
        """Issue a new access token from a valid refresh token"""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
            
        phone_hash = payload.get("sub")
        if not phone_hash:
            return None
            
        # Optional: check if user still exists/is active
        
        new_access_token = create_access_token(data={"sub": phone_hash})
        return {"access_token": new_access_token}

    def update_display_name(self, p_hash: str, display_name: str) -> dict:
        """
        Update user's display name using hash identifier.
        
        Returns:
            Dict with updated user info
        """
        user = self.auth_repo.update_display_name(p_hash, display_name)
        raw_phone = decrypt_data(user.encrypted_phone) if hasattr(user, "encrypted_phone") else None
        return {
            "phone": user.phone_hash,
            "raw_phone": raw_phone,
            "display_name": user.display_name
        }

    def update_fcm_token(self, p_hash: str, fcm_token: str) -> dict:
        """
        Update user's FCM token using hash identifier.
        
        Returns:
            Dict with updated user info
        """
        user = self.auth_repo.update_fcm_token(p_hash, fcm_token)
        return {
            "phone": user.phone_hash,
            "fcm_token": user.fcm_token
        }

    def get_user_info(self, p_hash: str) -> dict | None:
        """
        Get user information by phone hash identifier.
        
        Returns:
            Dict with user info or None if user doesn't exist
        """
        user = self.auth_repo.get_user_by_hash(p_hash)
        if not user:
            return None
        
        raw_phone = decrypt_data(user.encrypted_phone) if hasattr(user, "encrypted_phone") else None
        
        return {
            "phone": user.phone_hash,
            "raw_phone": raw_phone,
            "display_name": user.display_name,
            "verified": bool(user.verified)
        }
