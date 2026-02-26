import firebase_admin
from firebase_admin import auth, credentials
import os
import json

# Global variable to check if firebase is initialized
_FIREBASE_INITIALIZED = False

def initialize_firebase():
    global _FIREBASE_INITIALIZED
    if _FIREBASE_INITIALIZED:
        return True
        
    try:
        # 1. Try to load from environment variable (JSON string)
        # This is the safest way for production (e.g. Heroku, GCP, AWS)
        sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        if sa_json:
            cred_dict = json.loads(sa_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            _FIREBASE_INITIALIZED = True
            return True
            
        # 2. Try to load from a local file (for local development)
        # Point this to your downloaded service-account-key.json
        sa_file = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "firebase-key.json")
        if os.path.exists(sa_file):
            cred = credentials.Certificate(sa_file)
            firebase_admin.initialize_app(cred)
            _FIREBASE_INITIALIZED = True
            return True
            
        print("Warning: Firebase not initialized. Missing FIREBASE_SERVICE_ACCOUNT.")
        return False
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        return False

def verify_firebase_token(id_token: str) -> dict | None:
    """
    Verifies a Firebase ID Token sent from the frontend.
    Returns the decoded claims (including 'phone_number').
    """
    if not _FIREBASE_INITIALIZED:
        if not initialize_firebase():
            return None
            
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Firebase token verification failed: {str(e)}")
        return None
