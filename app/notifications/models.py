from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.domain.status import CheckInStatus


NotificationChannel = Literal["email", "sms", "whatsapp"]


@dataclass(frozen=True)
class NotificationRecipient:
    channel: NotificationChannel
    address: str
    name: str | None = None


@dataclass(frozen=True)
class StatusChangeEvent:
    user_phone: str
    new_status: CheckInStatus
    last_checkin_at: datetime | None
    created_at: datetime
    instructions: str | None = None


@dataclass(frozen=True)
class NotificationMessage:
    subject: str
    body: str
