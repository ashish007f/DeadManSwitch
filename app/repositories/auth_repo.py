"""
Authentication repository layer.

Encapsulates all user and OTP database operations.
Provides clean interface for auth service.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.schema import User, OTP
import random


class AuthRepository:
    """Manage user authentication and OTP operations"""
    
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, phone: str) -> User:
        """Get user by phone or create new user if doesn't exist"""
        if not phone:
            raise ValueError("Phone number is required")
        user = self.db.query(User).filter(User.phone_number == phone).first()
        if not user:
            user = User(phone_number=phone, display_name=phone, verified=0)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user

    def get_user_by_phone(self, phone: str) -> User | None:
        """Get user by phone number"""
        if not phone:
            raise ValueError("Phone number is required")
        return self.db.query(User).filter(User.phone_number == phone).first()

    def send_otp(self, phone: str) -> str:
        """
        Generate and store OTP for phone number.
        
        Returns:
            Generated OTP code (for dev/testing purposes)
        """
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Delete old unused OTPs for this phone
        self.db.query(OTP).filter(
            OTP.phone_number == phone,
            OTP.verified == 0
        ).delete(synchronize_session=False) 
        
        otp = OTP(phone_number=phone, code=code, expires_at=expires_at)
        self.db.add(otp)
        self.db.commit()
        return code

    def verify_otp(self, phone: str, code: str) -> tuple[bool, User | None]:
        """
        Verify OTP code for phone number.
        
        Returns:
            Tuple of (success: bool, user: User | None)
        """
        otp = self.db.query(OTP).filter(
            OTP.phone_number == phone,
            OTP.code == code,
            OTP.verified == 0
        ).first()
        
        if not otp:
            return False, None
        
        if otp.expires_at < datetime.utcnow():
            return False, None
        
        # Mark OTP as used
        otp.verified = 1
        
        # Get or create user and mark as verified
        user = self.get_or_create_user(phone)
        user.verified = 1
        
        self.db.commit()
        self.db.refresh(user)
        return True, user

    def update_display_name(self, phone: str, display_name: str) -> User:
        """Update user's display name"""
        user = self.get_or_create_user(phone)
        user.display_name = display_name
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_last_otp(self, phone: str) -> str | None:
        """Return the most recent OTP code for a phone (dev helper)"""
        otp = (
            self.db.query(OTP)
            .filter(OTP.phone_number == phone)
            .order_by(OTP.created_at.desc())
            .first()
        )
        return otp.code if otp else None
