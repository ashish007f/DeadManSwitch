"""
Repository layer for data access.

Encapsulates check-in, settings, and instructions database operations.
Provides clean interface for services.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.db.schema import CheckIn, Settings, Instructions, User
import json


class SettingsRepository:
    """Manage application settings"""
    
    def __init__(self, db: Session):
        self.db = db

    def _get_user(self, phone: str) -> User | None:
        """Get user by phone number (returns None if not found)"""
        if not phone:
            return None
        return self.db.query(User).filter(User.phone_number == phone).first()


    def get_or_create(self, phone: str) -> Settings | None:
        """Get settings for a user, create defaults if not exists. Returns None if user not found."""
        user = self._get_user(phone)
        if not user:
            return None
        settings = self.db.query(Settings).filter(Settings.user_id == user.id).first()
        if not settings:
            settings = Settings(
                user_id=user.id,
                checkin_interval_hours=48,
                missed_buffer_hours=1,
                grace_period_hours=24,
                contacts=None,
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings
    
    def update_settings(
        self,
        phone: str,
        checkin_interval_hours: int | None = None,
        missed_buffer_hours: int | None = None,
        grace_period_hours: int | None = None,
        contacts: list | None = None,
    ) -> Settings:
        """Update one or more settings fields"""
        settings = self.get_or_create(phone)
        if not settings:
            raise ValueError("User not found")
        if checkin_interval_hours is not None:
            settings.checkin_interval_hours = checkin_interval_hours
        if missed_buffer_hours is not None:
            settings.missed_buffer_hours = missed_buffer_hours
        if grace_period_hours is not None:
            settings.grace_period_hours = grace_period_hours
        if contacts is not None:
            # store as JSON string
            settings.contacts = json.dumps(contacts)

        self.db.commit()
        self.db.refresh(settings)
        return settings

    def read_settings(self, phone: str) -> dict | None:
        """Return settings as a dict with contacts deserialized for user. Returns None if user not found."""
        settings = self.get_or_create(phone)
        if not settings:
            return None
        data = {
            "id": settings.id,
            "checkin_interval_hours": settings.checkin_interval_hours,
            "missed_buffer_hours": settings.missed_buffer_hours,
            "grace_period_hours": settings.grace_period_hours,
            "contacts": None,
        }
        if settings.contacts:
            try:
                data["contacts"] = json.loads(settings.contacts)
            except Exception:
                data["contacts"] = []
        return data


class CheckInRepository:
    """Manage check-in records"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_checkin(self, phone: str, timestamp: datetime | None = None) -> CheckIn:
        """
        Record a check-in for a user.

        Phase 2 behavior: store only the most recent check-in per user.
        Implementation detail: update the newest row and delete any older rows.
        """
        if not phone:
            raise ValueError("Phone number is required")
        user = self.db.query(User).filter(User.phone_number == phone).first()
        if not user:
            raise ValueError("User not found")

        ts = timestamp or datetime.utcnow()

        rows = (
            self.db.query(CheckIn)
            .filter(CheckIn.user_id == user.id)
            .order_by(CheckIn.timestamp.desc(), CheckIn.id.desc())
            .all()
        )

        if not rows:
            checkin = CheckIn(timestamp=ts, user_id=user.id)
            self.db.add(checkin)
            self.db.commit()
            self.db.refresh(checkin)
            return checkin

        # Update the most recent row and delete the rest.
        newest = rows[0]
        newest.timestamp = ts
        for old in rows[1:]:
            self.db.delete(old)
        self.db.commit()
        self.db.refresh(newest)
        return newest
    
    def get_last_checkin(self, phone: str) -> CheckIn | None:
        """Get the most recent check-in for a user"""
        if not phone:
            raise ValueError("Phone number is required")
        user = self.db.query(User).filter(User.phone_number == phone).first()
        if not user:
            return None
        return (
            self.db.query(CheckIn)
            .filter(CheckIn.user_id == user.id)
            .order_by(CheckIn.timestamp.desc())
            .first()
        )
    
    def get_all_checkins(self, phone: str) -> list[CheckIn]:
        """Return at most one (the most recent) check-in for a user."""
        if not phone:
            raise ValueError("Phone number is required")
        user = self.db.query(User).filter(User.phone_number == phone).first()
        if not user:
            return []
        last = (
            self.db.query(CheckIn)
            .filter(CheckIn.user_id == user.id)
            .order_by(CheckIn.timestamp.desc(), CheckIn.id.desc())
            .first()
        )
        return [last] if last else []


class InstructionsRepository:
    """Manage instructions for trusted contacts"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_instructions(self, phone: str) -> Instructions | None:
        """Get instructions for a user, create if not exists. Returns None if user not found."""
        if not phone:
            raise ValueError("Phone number is required")
        user = self.db.query(User).filter(User.phone_number == phone).first()
        if not user:
            return None
        instructions = self.db.query(Instructions).filter(Instructions.user_id == user.id).first()
        if not instructions:
            instructions = Instructions(user_id=user.id, content=None)
            self.db.add(instructions)
            self.db.commit()
            self.db.refresh(instructions)
        return instructions
    
    def update_content(self, content: str, phone: str) -> Instructions:
        """Update instructions content for a user"""
        instructions = self.get_or_create_instructions(phone)
        if not instructions:
            raise ValueError("User not found")
        instructions.content = content
        instructions.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(instructions)
        return instructions
