"""
Check-in service layer for Cloud Firestore.

Orchestrates check-in operations (recording, status, settings, instructions).
"""

from datetime import datetime, timedelta, timezone
from google.cloud import firestore

from app.repositories.checkin_repo import (
    CheckInRepository,
    SettingsRepository,
    InstructionsRepository,
)
from app.domain.status import compute_status, hours_until_due, CheckInStatus
from app.domain.models import (
    CheckInResponse,
    StatusResponse,
    SettingsResponse,
    InstructionsResponse,
    SettingsUpdate,
)


class CheckInService:
    """Orchestrate check-in operations using Firestore"""
    
    def __init__(self, db: firestore.Client):
        self.db = db
        self.checkin_repo = CheckInRepository(db)
        self.settings_repo = SettingsRepository(db)
        self.instructions_repo = InstructionsRepository(db)
    
    def record_checkin(self, phone: str | None = None, hours_ago: float | None = None) -> CheckInResponse:
        """Record a new check-in and return current status."""
        if not phone:
            raise ValueError("Phone number is required to record check-in")
            
        ts = None
        if hours_ago is not None:
            ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)

        checkin = self.checkin_repo.record_checkin(phone=phone, timestamp=ts)
        status = self.compute_current_status(phone=phone)
        settings = self.settings_repo.get_or_create(phone)

        return CheckInResponse(
            timestamp=checkin.timestamp,
            status=status,
            hours_until_due=hours_until_due(
                checkin.timestamp,
                settings.checkin_interval_hours,
                missed_buffer_hours=settings.missed_buffer_hours,
                grace_period_hours=settings.grace_period_hours,
            ),
        )
    
    def get_last_checkin(self, phone: str | None = None) -> datetime | None:
        """Get timestamp of last check-in for a user"""
        if not phone:
            raise ValueError("Phone number is required to get check-in")
        last = self.checkin_repo.get_last_checkin(phone)
        return last.timestamp if last else None
    
    def compute_current_status(self, phone: str | None = None) -> CheckInStatus:
        """Compute current check-in status."""
        if not phone:
            raise ValueError("Phone number is required to compute status")
        last_checkin = self.get_last_checkin(phone)
        settings = self.settings_repo.get_or_create(phone)

        return compute_status(
            last_checkin,
            settings.checkin_interval_hours,
            missed_buffer_hours=settings.missed_buffer_hours,
            grace_period_hours=settings.grace_period_hours,
        )
    
    def get_status(self, phone: str | None = None) -> StatusResponse:
        """Get full status information."""
        if not phone:
            raise ValueError("Phone number is required to get status")
        last_checkin = self.get_last_checkin(phone)
        settings = self.settings_repo.get_or_create(phone)
        status = self.compute_current_status(phone=phone)
        
        remaining = hours_until_due(
            last_checkin,
            settings.checkin_interval_hours,
            missed_buffer_hours=settings.missed_buffer_hours,
            grace_period_hours=settings.grace_period_hours,
        )

        return StatusResponse(
            status=status,
            last_checkin=last_checkin,
            hours_until_due=remaining,
            interval_hours=settings.checkin_interval_hours,
        )
    
    def update_settings(self, update: SettingsUpdate, phone: str | None = None) -> SettingsResponse:
        """Update application settings."""
        if not phone:
            raise ValueError("Phone number is required to update settings")

        settings = self.settings_repo.update_settings(
            phone=phone,
            checkin_interval_hours=update.checkin_interval_hours,
            missed_buffer_hours=update.missed_buffer_hours,
            grace_period_hours=update.grace_period_hours,
            contacts=update.contacts,
        )

        return SettingsResponse(
            checkin_interval_hours=settings.checkin_interval_hours,
            missed_buffer_hours=settings.missed_buffer_hours,
            grace_period_hours=settings.grace_period_hours,
            contacts=settings.contacts or [],
        )
    
    def get_settings(self, phone: str | None = None) -> SettingsResponse:
        """Get current application settings."""
        if not phone:
            raise ValueError("Phone number is required to get settings")
        data = self.settings_repo.read_settings(phone)
        return SettingsResponse(
            checkin_interval_hours=data["checkin_interval_hours"],
            missed_buffer_hours=data["missed_buffer_hours"],
            grace_period_hours=data["grace_period_hours"],
            contacts=data.get("contacts") or [],
        )
    
    def save_instructions(self, content: str, phone: str | None = None) -> InstructionsResponse:
        """Save instructions for trusted contacts."""
        if not phone:
            raise ValueError("Phone number is required to save instructions")
        instructions = self.instructions_repo.update_content(content, phone=phone)
        return InstructionsResponse(
            content=instructions.content,
            updated_at=instructions.updated_at,
        )
    
    def get_instructions(self, phone: str | None = None) -> InstructionsResponse:
        """Get instructions for trusted contacts."""
        if not phone:
            raise ValueError("Phone number is required to get instructions")
        instructions = self.instructions_repo.get_or_create_instructions(phone)
        return InstructionsResponse(
            content=instructions.content,
            updated_at=instructions.updated_at,
        )
