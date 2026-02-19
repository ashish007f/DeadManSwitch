"""
Check-in service layer.

Orchestrates check-in operations (recording, status, settings, instructions).
Uses check-in repositories and domain logic.
Separated from authentication service for modularity.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

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
import json


class CheckInService:
    """Orchestrate check-in operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.checkin_repo = CheckInRepository(db)
        self.settings_repo = SettingsRepository(db)
        self.instructions_repo = InstructionsRepository(db)
    
    def record_checkin(self, phone: str | None = None, hours_ago: int | None = None) -> CheckInResponse:
        """
        Record a new check-in and return current status.
        
        Returns:
            CheckInResponse with timestamp and updated status
        """
        if not phone:
            raise ValueError("Phone number is required to record check-in")
        # optional testing helper: create a checkin with a timestamp offset
        ts = None
        if hours_ago is not None:
            ts = datetime.utcnow() - timedelta(hours=hours_ago)

        checkin = self.checkin_repo.record_checkin(phone=phone, timestamp=ts)
        status = self.compute_current_status(phone=phone)

        settings = self.settings_repo.get_or_create(phone)
        missed_buffer = getattr(settings, "missed_buffer_hours", 1)
        grace_period = getattr(settings, "grace_period_hours", 24)

        return CheckInResponse(
            timestamp=checkin.timestamp,
            status=status,
            hours_until_due=hours_until_due(
                checkin.timestamp,
                settings.checkin_interval_hours,
                missed_buffer_hours=missed_buffer,
                grace_period_hours=grace_period,
            ),
        )
    
    def get_last_checkin(self, phone: str | None = None) -> datetime | None:
        """Get timestamp of last check-in for a user"""
        if not phone:
            raise ValueError("Phone number is required to get check-in")
        last = self.checkin_repo.get_last_checkin(phone)
        return last.timestamp if last else None
    
    def compute_current_status(self, phone: str | None = None) -> CheckInStatus:
        """
        Compute current check-in status.

        Uses the current `Settings` values (`checkin_interval_hours`,
        `missed_buffer_hours`, and `grace_period_hours`) to evaluate the
        status lifecycle: SAFE → DUE_SOON → MISSED → GRACE_PERIOD → NOTIFIED.

        Returns:
            CheckInStatus enum value
        """
        if not phone:
            raise ValueError("Phone number is required to compute status")
        last_checkin = self.get_last_checkin(phone)
        settings = self.settings_repo.get_or_create(phone)
        if not settings:
            raise ValueError(f"User not found: {phone}")

        missed_buffer = getattr(settings, "missed_buffer_hours", 1)
        grace_period = getattr(settings, "grace_period_hours", 24)

        return compute_status(
            last_checkin,
            settings.checkin_interval_hours,
            missed_buffer_hours=missed_buffer,
            grace_period_hours=grace_period,
        )
    
    def get_status(self, phone: str | None = None) -> StatusResponse:
        """
        Get full status information.
        
        Returns:
            StatusResponse with status, last_checkin, hours remaining, interval
        """
        if not phone:
            raise ValueError("Phone number is required to get status")
        last_checkin = self.get_last_checkin(phone)
        settings = self.settings_repo.get_or_create(phone)
        if not settings:
            raise ValueError(f"User not found: {phone}")
        status = self.compute_current_status(phone=phone)
        missed_buffer = getattr(settings, "missed_buffer_hours", 1)
        grace_period = getattr(settings, "grace_period_hours", 24)
        remaining = hours_until_due(
            last_checkin,
            settings.checkin_interval_hours,
            missed_buffer_hours=missed_buffer,
            grace_period_hours=grace_period,
        )

        return StatusResponse(
            status=status,
            last_checkin=last_checkin,
            hours_until_due=remaining,
            interval_hours=settings.checkin_interval_hours,
        )
    
    def update_settings(self, update: SettingsUpdate, phone: str | None = None) -> SettingsResponse:
        """
        Update application settings.

        Accepts a `SettingsUpdate` model and updates any provided fields
        (check-in interval, missed buffer, grace period, and contacts).

        Returns:
            SettingsResponse with the stored settings (contacts are deserialized)
        """
        if not phone:
            raise ValueError("Phone number is required to update settings")
        contacts = None
        if update.contacts is not None:
            contacts = update.contacts

        settings = self.settings_repo.update_settings(
            phone=phone,
            checkin_interval_hours=update.checkin_interval_hours,
            missed_buffer_hours=update.missed_buffer_hours,
            grace_period_hours=update.grace_period_hours,
            contacts=contacts,
        )

        result = SettingsResponse(
            checkin_interval_hours=settings.checkin_interval_hours,
            missed_buffer_hours=settings.missed_buffer_hours,
            grace_period_hours=settings.grace_period_hours,
            contacts=None,
        )
        if settings.contacts:
            try:
                result.contacts = json.loads(settings.contacts)
            except Exception:
                result.contacts = []

        return result
    
    def get_settings(self, phone: str | None = None) -> SettingsResponse:
        """
        Get current application settings.

        Returns:
            SettingsResponse containing `checkin_interval_hours`,
            `missed_buffer_hours`, `grace_period_hours`, and `contacts`.
        """
        if not phone:
            raise ValueError("Phone number is required to get settings")
        data = self.settings_repo.read_settings(phone)
        if not data:
            raise ValueError(f"User not found: {phone}")
        return SettingsResponse(
            checkin_interval_hours=data["checkin_interval_hours"],
            missed_buffer_hours=data["missed_buffer_hours"],
            grace_period_hours=data["grace_period_hours"],
            contacts=data.get("contacts"),
        )
    
    def save_instructions(self, content: str, phone: str | None = None) -> InstructionsResponse:
        """
        Save instructions for trusted contacts.
        
        Args:
            content: Instructions text
            
        Returns:
            InstructionsResponse with saved content
        """
        if not phone:
            raise ValueError("Phone number is required to save instructions")
        instructions = self.instructions_repo.update_content(content, phone=phone)
        return InstructionsResponse(
            content=instructions.content,
            updated_at=instructions.updated_at,
        )
    
    def get_instructions(self, phone: str | None = None) -> InstructionsResponse:
        """
        Get instructions for trusted contacts.
        
        Returns:
            InstructionsResponse with content and timestamp
        """
        if not phone:
            raise ValueError("Phone number is required to get instructions")
        instructions = self.instructions_repo.get_or_create_instructions(phone)
        return InstructionsResponse(
            content=instructions.content,
            updated_at=instructions.updated_at,
        )

