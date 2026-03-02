import hashlib
import phonenumbers
import jwt
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from app.config import settings

def normalize_phone(phone: str, default_region: str = "US") -> str:
    """
    Normalize phone number to E.164 format (+1234567890).
    Raises ValueError if invalid.
    """
    try:
        phone = phone.strip()
        # If the number doesn't start with +, assume it's from the default region
        if not phone.startswith("+"):
            parsed = phonenumbers.parse(phone, default_region)
        else:
            parsed = phonenumbers.parse(phone, None)
            
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number format")
            
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception as e:
        raise ValueError(f"Could not parse phone number: {str(e)}")

def hash_phone(normalized_phone: str) -> str:
    """
    Generate a SHA-256 hash of the normalized phone number + salt for privacy.
    This is used as the primary identifier in the database.
    """
    salted = f"{normalized_phone}{settings.phone_salt}"
    return hashlib.sha256(salted.encode()).hexdigest()

def secure_phone_identity(phone: str) -> Tuple[str, str]:
    """
    Takes a raw phone number, normalizes it, and hashes it.
    Returns: (normalized_phone, hashed_phone)
    """
    norm = normalize_phone(phone)
    h = hash_phone(norm)
    return norm, h

def create_access_token(data: dict) -> str:
    """Create a short-lived access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.PyJWTError:
        return None
