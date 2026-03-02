import base64
import hashlib
from cryptography.fernet import Fernet
from app.config import settings

# Derive a 32-byte key from the application's secret key
# Fernet keys must be 32 url-safe base64-encoded bytes
def _get_fernet() -> Fernet:
    """Generate a Fernet instance using the application's secret key."""
    key = hashlib.sha256(settings.secret_key.encode()).digest()
    key_base64 = base64.urlsafe_b64encode(key)
    return Fernet(key_base64)

def encrypt_data(data: str | None) -> str | None:
    """Encrypt a string using AES (Fernet)."""
    if data is None or data == "":
        return data
    
    f = _get_fernet()
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str | None) -> str | None:
    """Decrypt an AES-encrypted string (Fernet)."""
    if encrypted_data is None or encrypted_data == "":
        return encrypted_data
    
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        # If decryption fails (e.g. key changed or not encrypted), 
        # return original for migration/safety or None
        print(f"Decryption failed: {str(e)}")
        return encrypted_data # Fallback to original
