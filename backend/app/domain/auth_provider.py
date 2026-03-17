import firebase_admin
from firebase_admin import auth, credentials, app_check
import os
import json
from app.config import settings

# Global variable to check if firebase is initialized
_FIREBASE_INITIALIZED = False

def initialize_firebase():
    global _FIREBASE_INITIALIZED
    
    # 0. Check if already initialized by this app or firebase_admin
    if _FIREBASE_INITIALIZED:
        return True
    try:
        firebase_admin.get_app()
        _FIREBASE_INITIALIZED = True
        return True
    except ValueError:
        pass # Not initialized yet
        
    try:
        # 1. Try to load from environment variable (JSON string)
        # This is the safest way for production (e.g. Fly.io, Heroku, Railway)
        sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or os.getenv("FIREBASE_SERVICE_ACCOUNT")
        if sa_json:
            try:
                # Remove potential surrounding quotes and whitespace from shell cat
                sa_json = sa_json.strip()
                if sa_json.startswith("'") and sa_json.endswith("'"):
                    sa_json = sa_json[1:-1]
                
                cred_dict = json.loads(sa_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                _FIREBASE_INITIALIZED = True
                print("✓ Firebase initialized from Environment Variable")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Error: FIREBASE_SERVICE_ACCOUNT_JSON is not a valid JSON string: {e}")
                # Print first 20 chars for debugging (safely)
                print(f"   Starts with: {sa_json[:20]}...")
            
        # 2. Try to load from a local file (for local development)
        sa_file = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "firebase-key.json")
        if os.path.exists(sa_file):
            cred = credentials.Certificate(sa_file)
            firebase_admin.initialize_app(cred)
            _FIREBASE_INITIALIZED = True
            print(f"✓ Firebase initialized from local file: {sa_file}")
            return True
            
        # 3. Fallback to default credentials (works on GCP/Cloud Run)
        try:
            # Explicitly set project_id to ensure we match the frontend
            project_id = os.getenv("FIRESTORE_PROJECT_ID")
            firebase_admin.initialize_app(options={'projectId': project_id} if project_id else None)
            _FIREBASE_INITIALIZED = True
            print(f"✓ Firebase initialized with Default Credentials (Project: {project_id or 'Ambient'})")
            return True
        except Exception as e:
            print(f"⚠ Warning: Firebase fallback failed: {e}")
            
        print("⚠ Warning: Firebase not initialized. Missing environment variable and local file.")
        return False
    except Exception as e:
        print(f"❌ Error initializing Firebase: {str(e)}")
        return False

def verify_app_check_token(app_check_token: str) -> bool:
    """
    Verifies the Firebase App Check token.
    """
    # Determine if App Check should be enforced
    enforce = settings.enforce_app_check

    if not app_check_token:
        if enforce:
            print("❌ App Check token is missing and enforcement is ON.")
            return False
        return True # Allow if not enforced

    if not _FIREBASE_INITIALIZED:
        if not initialize_firebase():
            return False
            
    try:
        app_check.verify_token(app_check_token)
        return True
    except Exception as e:
        print(f"App Check verification failed: {str(e)}")
        return not enforce

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
