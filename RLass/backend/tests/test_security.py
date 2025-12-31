import pytest
from backend.utils import security

def test_generate_api_key_length_and_uniqueness():
    key1 = security.generate_api_key()
    key2 = security.generate_api_key()
    assert isinstance(key1, str)
    assert isinstance(key2, str)
    assert key1 != key2  # Should be unique
    assert len(key1) >= security.API_KEY_LENGTH  # token_urlsafe may be longer

def test_hash_api_key_consistency():
    key = "testkey123"
    hashed1 = security.hash_api_key(key)
    hashed2 = security.hash_api_key(key)
    assert isinstance(hashed1, str)
    assert hashed1 == hashed2
    assert len(hashed1) == 64  # sha256 hex digest length

def test_verify_api_key_success():
    key = "anotherkey456"
    hashed = security.hash_api_key(key)
    assert security.verify_api_key(key, hashed)

def test_verify_api_key_failure():
    key = "key1"
    wrong_key = "key2"
    hashed = security.hash_api_key(key)
    assert not security.verify_api_key(wrong_key, hashed)
