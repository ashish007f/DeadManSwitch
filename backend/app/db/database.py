"""
Database initialization for Cloud Firestore.

Replaces SQLAlchemy engine with the Firestore client.
"""

from google.cloud import firestore
from typing import Generator
import os

from app.domain.auth_provider import initialize_firebase

# Global firestore client
_db_client: firestore.Client | None = None

def get_firestore_client() -> firestore.Client:
    """
    Get or initialize the Firestore client with proper credentials.
    """
    global _db_client
    if _db_client:
        return _db_client
        
    # Ensure Firebase is initialized
    if not initialize_firebase():
        raise RuntimeError("Failed to initialize Firebase before creating Firestore client")
        
    # Create the client with credentials
    # 1. Try from environment variable JSON string
    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if sa_json:
        try:
            import json
            from google.oauth2 import service_account
            cred_dict = json.loads(sa_json)
            credentials = service_account.Credentials.from_service_account_info(cred_dict)
            _db_client = firestore.Client(credentials=credentials, project=cred_dict.get("project_id"))
            return _db_client
        except Exception as e:
            print(f"⚠ Could not create Firestore client from env var: {e}")

    # 2. Try from local file
    sa_file = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "firebase-key.json")
    if os.path.exists(sa_file):
        try:
            _db_client = firestore.Client.from_service_account_json(sa_file)
            return _db_client
        except Exception as e:
            print(f"⚠ Could not create Firestore client from local file: {e}")

    # 3. Fallback to default credentials (works on GCP/Cloud Run)
    _db_client = firestore.Client()
    return _db_client

def get_db() -> Generator[firestore.Client, None, None]:
    """
    Dependency injection for FastAPI routes.
    
    Yields:
        Firestore Client
    """
    db = get_firestore_client()
    yield db
    # Firestore client handles its own connection pooling, no need to 'close' manually
