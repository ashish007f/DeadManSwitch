"""
Notification log repository for Cloud Firestore.

Stores records of sent notifications to prevent repeated sends.
"""

from datetime import datetime, timezone
from google.cloud import firestore
from app.domain.security import secure_phone_identity


class NotificationLogRepository:
    """Manage notification logs in Firestore"""
    
    def __init__(self, db: firestore.Client):
        self.db = db
        self.users_collection = self.db.collection("users")

    def _get_notif_log_ref(self, phone: str):
        _, p_hash = secure_phone_identity(phone)
        return self.users_collection.document(p_hash).collection("notification_logs")

    def has_sent(self, *, phone: str, last_checkin_at: datetime, status: str) -> bool:
        """Check if a specific notification was already sent for this check-in cycle."""
        # We can use a composite key approach or just query
        # Since we use ISO strings for timestamps in Firestore docs or just timestamps
        logs_ref = self._get_notif_log_ref(phone)
        
        # Firestore query
        query = logs_ref.where("last_checkin_at", "==", last_checkin_at).where("status", "==", status).limit(1)
        docs = list(query.get())
        return len(docs) > 0

    def record_sent(self, *, phone: str, last_checkin_at: datetime, status: str) -> None:
        """Record that a notification was sent."""
        logs_ref = self._get_notif_log_ref(phone)
        logs_ref.add({
            "last_checkin_at": last_checkin_at,
            "status": status,
            "notified_at": datetime.now(timezone.utc)
        })
