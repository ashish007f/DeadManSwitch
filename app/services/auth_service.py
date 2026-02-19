"""
Authentication service layer.

Orchestrates authentication workflows (signup, login, OTP verification).
Handles authentication business logic.
"""

from sqlalchemy.orm import Session
from app.repositories.auth_repo import AuthRepository


class AuthService:
    """Orchestrate authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_repo = AuthRepository(db)
    
    def send_otp(self, phone: str) -> dict:
        """
        Initiate signup/login by sending OTP to phone.
        
        Returns:
            Dict with "ok": bool and "otp": code (for dev mode)
        """
        code = self.auth_repo.send_otp(phone)
        print(f"[OTP] Phone: {phone}, Code: {code}")
        return {"ok": True, "otp": code}

    def verify_otp(self, phone: str, code: str) -> dict | None:
        """
        Verify OTP and authenticate user.
        
        Returns:
            Dict with user info (phone, display_name) or None if invalid
        """
        ok, user = self.auth_repo.verify_otp(phone, code)
        if not ok or not user:
            return None
        return {
            "phone": user.phone_number,
            "display_name": user.display_name
        }

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
