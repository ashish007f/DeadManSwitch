"""
Authentication repository layer for Cloud Firestore.

Encapsulates all user document operations in Firestore.
"""

from datetime import datetime, timezone
from google.cloud import firestore
from types import SimpleNamespace
from app.domain.security import secure_phone_identity


class AuthRepository:
    """Manage user authentication operations in Firestore"""
    
    def __init__(self, db: firestore.Client):
        self.db = db
        self.collection = self.db.collection("users")

    def _map_to_namespace(self, data: dict) -> SimpleNamespace:
        """Map Firestore dictionary to a SimpleNamespace for ORM-like attribute access"""
        return SimpleNamespace(**data)

    def get_or_create_user(self, phone: str) -> SimpleNamespace:
        """Get user by phone hash or create new user document"""
        if not phone:
            raise ValueError("Phone number is required")
        
        normalized, p_hash = secure_phone_identity(phone)
        
        # Identity is driven by phone_hash for privacy
        doc_ref = self.collection.document(p_hash)
        doc = doc_ref.get()
            
        if not doc.exists:
            user_data = {
                "phone_number": normalized, 
                "phone_hash": p_hash,
                "display_name": normalized, 
                "verified": 1,
                "created_at": datetime.now(timezone.utc),
                "fcm_token": None,
                "last_login": datetime.now(timezone.utc)
            }
            doc_ref.set(user_data)
            return self._map_to_namespace(user_data)
                
        return self._map_to_namespace(doc.to_dict())

    def get_user_by_phone(self, phone: str) -> SimpleNamespace | None:
        """Get user by phone hash"""
        if not phone:
            raise ValueError("Phone number is required")
        
        _, p_hash = secure_phone_identity(phone)
        doc = self.collection.document(p_hash).get()
        if doc.exists:
            return self._map_to_namespace(doc.to_dict())
        return None

    def update_display_name(self, phone: str, display_name: str) -> SimpleNamespace:
        """Update user's display name"""
        _, p_hash = secure_phone_identity(phone)
        doc_ref = self.collection.document(p_hash)
        
        doc_ref.update({"display_name": display_name})
        return self._map_to_namespace(doc_ref.get().to_dict())

    def update_fcm_token(self, phone: str, fcm_token: str) -> SimpleNamespace:
        """Update user's FCM token for push notifications"""
        _, p_hash = secure_phone_identity(phone)
        doc_ref = self.collection.document(p_hash)
        
        doc_ref.update({"fcm_token": fcm_token})
        return self._map_to_namespace(doc_ref.get().to_dict())
        
    def update_last_login(self, phone: str) -> None:
        """Update last login timestamp"""
        _, p_hash = secure_phone_identity(phone)
        self.collection.document(p_hash).update({"last_login": datetime.now(timezone.utc)})
