import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import get_settings


def get_cipher() -> Fernet:
    """Derive a deterministic 32-byte url-safe base64 key from encryption_key or jwt_secret."""
    settings = get_settings()
    raw_key = settings.encryption_key or settings.jwt_secret
    # SHA-256 hash ensures exactly 32 bytes
    derived = hashlib.sha256(raw_key.encode("utf-8")).digest()
    key_b64 = base64.urlsafe_b64encode(derived)
    return Fernet(key_b64)


def encrypt_token(plain_token: str | None) -> str | None:
    """Encrypt a sensitive OAuth token before storing in the database."""
    if not plain_token:
        return None
    cipher = get_cipher()
    return cipher.encrypt(plain_token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str | None) -> str | None:
    """Decrypt a stored OAuth token when making API requests."""
    if not encrypted_token:
        return None
    try:
        cipher = get_cipher()
        return cipher.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except Exception:
        return None
