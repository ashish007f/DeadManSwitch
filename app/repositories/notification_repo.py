"""
Notification log repository.

Stores lightweight records of sent notifications to prevent repeated sends.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.schema import NotificationLog


class NotificationLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def has_sent(self, *, user_id: int, last_checkin_at: datetime, status: str) -> bool:
        row = (
            self.db.query(NotificationLog)
            .filter(
                NotificationLog.user_id == user_id,
                NotificationLog.last_checkin_at == last_checkin_at,
                NotificationLog.status == status,
            )
            .first()
        )
        return row is not None

    def record_sent(self, *, user_id: int, last_checkin_at: datetime, status: str) -> NotificationLog:
        row = NotificationLog(user_id=user_id, last_checkin_at=last_checkin_at, status=status)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
