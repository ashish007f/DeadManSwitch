"""
Authentication repository layer.

Encapsulates all user and OTP database operations.
Provides clean interface for auth service.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.schema import User
from app.domain.security import secure_phone_identity


class AuthRepository:
    """Manage user authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, phone: str) -> User:
        """Get user by phone hash or create new user with hashed identity"""
        if not phone:
            raise ValueError("Phone number is required")
        
        normalized, p_hash = secure_phone_identity(phone)
        
        # Identity is driven by phone_hash for privacy
        user = self.db.query(User).filter(User.phone_hash == p_hash).first()
            
        if not user:
            user = User(
                phone_number=normalized, 
                phone_hash=p_hash,
                display_name=normalized, 
                verified=1 # Always verified in Firebase flow
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
                
        return user

    def get_user_by_phone(self, phone: str) -> User | None:
        """Get user by phone hash"""
        if not phone:
            raise ValueError("Phone number is required")
        
        _, p_hash = secure_phone_identity(phone)
        return self.db.query(User).filter(User.phone_hash == p_hash).first()

    def update_display_name(self, phone: str, display_name: str) -> User:
        """Update user's display name"""
        user = self.get_or_create_user(phone)
        user.display_name = display_name
        self.db.commit()
        self.db.refresh(user)
        return user
