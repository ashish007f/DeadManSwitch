"""
Tests for Encryption utility.
"""

from app.domain.encryption import encrypt_data, decrypt_data

def test_encryption_decryption():
    original_text = "Secret bank account: 123456"
    
    # Encrypt
    encrypted = encrypt_data(original_text)
    assert encrypted != original_text
    assert isinstance(encrypted, str)
    
    # Decrypt
    decrypted = decrypt_data(encrypted)
    assert decrypted == original_text

def test_encryption_empty_values():
    assert encrypt_data(None) is None
    assert encrypt_data("") == ""
    assert decrypt_data(None) is None
    assert decrypt_data("") == ""

def test_decryption_fallback():
    # If text is not encrypted, it should return original (current behavior)
    text = "Just plain text"
    assert decrypt_data(text) == text
