"""
Repository layer for Cloud Firestore data access.

Encapsulates check-in, settings, and instructions Firestore operations.
"""

from datetime import datetime, timezone
from google.cloud import firestore
from types import SimpleNamespace
from app.domain.security import secure_phone_identity
from app.domain.encryption import encrypt_data, decrypt_data


class FirestoreBaseRepository:
    """Base logic for Firestore repositories"""
    def __init__(self, db: firestore.Client):
        self.db = db
        self.users_collection = self.db.collection("users")

    def _get_user_ref(self, p_hash: str) -> firestore.DocumentReference:
        """Get document reference for a user by their identity hash"""
        return self.users_collection.document(p_hash)


class SettingsRepository(FirestoreBaseRepository):
    """Manage application settings in Firestore"""
    
    def get_or_create(self, p_hash: str) -> SimpleNamespace:
        """Get settings for a user, create defaults if not exists."""
        user_ref = self._get_user_ref(p_hash)
        settings_ref = user_ref.collection("config").document("settings")
        doc = settings_ref.get()
        
        if not doc.exists:
            data = {
                "checkin_interval_hours": 48.0,
                "missed_buffer_hours": 1.0,
                "grace_period_hours": 24.0,
                "contacts": [],
            }
            settings_ref.set(data)
            return SimpleNamespace(**data)
            
        data = doc.to_dict()
        if data.get("contacts"):
            data["contacts"] = [decrypt_data(c) for c in data["contacts"]]
        return SimpleNamespace(**data)
    
    def update_settings(
        self,
        p_hash: str,
        checkin_interval_hours: float | None = None,
        missed_buffer_hours: float | None = None,
        grace_period_hours: float | None = None,
        contacts: list | None = None,
    ) -> SimpleNamespace:
        """Update one or more settings fields"""
        user_ref = self._get_user_ref(p_hash)
        settings_ref = user_ref.collection("config").document("settings")
        
        update_data = {}
        if checkin_interval_hours is not None:
            update_data["checkin_interval_hours"] = float(checkin_interval_hours)
        if missed_buffer_hours is not None:
            update_data["missed_buffer_hours"] = float(missed_buffer_hours)
        if grace_period_hours is not None:
            update_data["grace_period_hours"] = float(grace_period_hours)
        if contacts is not None:
            update_data["contacts"] = [encrypt_data(c) for c in contacts]

        if not settings_ref.get().exists:
            # Create with defaults first if doesn't exist
            self.get_or_create(p_hash)
            
        settings_ref.update(update_data)
        
        # Return decrypted version
        data = settings_ref.get().to_dict()
        if data.get("contacts"):
            data["contacts"] = [decrypt_data(c) for c in data["contacts"]]
        return SimpleNamespace(**data)

    def read_settings(self, p_hash: str) -> dict:
        """Return settings as a dict. Creates defaults if not exists."""
        settings = self.get_or_create(p_hash)
        return {
            "checkin_interval_hours": settings.checkin_interval_hours,
            "missed_buffer_hours": settings.missed_buffer_hours,
            "grace_period_hours": settings.grace_period_hours,
            "contacts": settings.contacts or [],
        }


class CheckInRepository(FirestoreBaseRepository):
    """Manage check-in records in Firestore"""
    
    def record_checkin(self, p_hash: str, timestamp: datetime | None = None) -> SimpleNamespace:
        """
        Record a check-in for a user.
        Phase 2 behavior: store only the most recent check-in.
        """
        user_ref = self._get_user_ref(p_hash)
        checkin_ref = user_ref.collection("data").document("last_checkin")
        
        ts = timestamp or datetime.now(timezone.utc)
        data = {"timestamp": ts}
        checkin_ref.set(data)
        
        return SimpleNamespace(**data)
    
    def get_last_checkin(self, p_hash: str) -> SimpleNamespace | None:
        """Get the most recent check-in for a user"""
        user_ref = self._get_user_ref(p_hash)
        doc = user_ref.collection("data").document("last_checkin").get()
        if doc.exists:
            return SimpleNamespace(**doc.to_dict())
        return None
    
    def get_all_checkins(self, p_hash: str) -> list[SimpleNamespace]:
        """Return at most one (the most recent) check-in for a user."""
        last = self.get_last_checkin(p_hash)
        return [last] if last else []


class InstructionsRepository(FirestoreBaseRepository):
    """Manage instructions for trusted contacts in Firestore"""
    
    def get_or_create_instructions(self, p_hash: str) -> SimpleNamespace:
        """Get instructions for a user, create if not exists."""
        user_ref = self._get_user_ref(p_hash)
        instr_ref = user_ref.collection("config").document("instructions")
        doc = instr_ref.get()
        
        if not doc.exists:
            data = {"content": None, "updated_at": datetime.now(timezone.utc)}
            instr_ref.set(data)
            return SimpleNamespace(**data)
            
        return SimpleNamespace(**doc.to_dict())
    
    def update_content(self, content: str, p_hash: str) -> SimpleNamespace:
        """Update instructions content for a user"""
        user_ref = self._get_user_ref(p_hash)
        instr_ref = user_ref.collection("config").document("instructions")
        
        data = {
            "content": content,
            "updated_at": datetime.now(timezone.utc)
        }
        
        if not instr_ref.get().exists:
            instr_ref.set(data)
        else:
            instr_ref.update(data)
            
        return SimpleNamespace(**data)
