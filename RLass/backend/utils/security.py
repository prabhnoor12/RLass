import secrets
import hashlib

API_KEY_LENGTH = 32


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(API_KEY_LENGTH)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed: str) -> bool:
    """Verify an API key against its hash."""
    return hash_api_key(api_key) == hashed
