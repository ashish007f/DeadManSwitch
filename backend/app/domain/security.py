import hashlib
import phonenumbers
from typing import Tuple

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
    Generate a SHA-256 hash of the normalized phone number for privacy.
    This is used as the primary identifier in the database.
    """
    return hashlib.sha256(normalized_phone.encode()).hexdigest()

def secure_phone_identity(phone: str) -> Tuple[str, str]:
    """
    Takes a raw phone number, normalizes it, and hashes it.
    Returns: (normalized_phone, hashed_phone)
    """
    norm = normalize_phone(phone)
    h = hash_phone(norm)
    return norm, h
