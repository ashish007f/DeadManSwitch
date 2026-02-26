"""
Pydantic domain models for API requests/responses.

These are distinct from SQLAlchemy ORM models.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.domain.status import CheckInStatus


class SettingsUpdate(BaseModel):
    """Settings update request (all fields optional)"""
    checkin_interval_hours: int | None = None
    missed_buffer_hours: int | None = None
    grace_period_hours: int | None = None
    contacts: List[str] | None = None


class SettingsResponse(BaseModel):
    """Settings response"""
    checkin_interval_hours: int
    missed_buffer_hours: int
    grace_period_hours: int
    contacts: List[str] | None = None


class CheckInRequest(BaseModel):
    """Check-in request - minimal payload, all fields optional"""
    # Optional testing field: create a check-in 'hours_ago' hours in the past
    hours_ago: int | None = None


class CheckInResponse(BaseModel):
    """Check-in response"""
    timestamp: datetime
    status: CheckInStatus
    hours_until_due: float


class StatusResponse(BaseModel):
    """Current system status"""
    status: CheckInStatus
    last_checkin: datetime | None
    hours_until_due: float
    interval_hours: int


class InstructionsResponse(BaseModel):
    """Instructions content"""
    content: str | None
    updated_at: datetime | None


class InstructionsUpdate(BaseModel):
    """Instructions update request"""
    content: str


class LoginRequest(BaseModel):
    """Login request: username is unique id, display_name is optional"""
    username: str
    display_name: str | None = None


class UserResponse(BaseModel):
    """User info response"""
    username: str
    display_name: str | None = None
