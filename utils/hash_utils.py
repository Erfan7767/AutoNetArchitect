"""Cryptographic hashing utilities."""
import hashlib
def sha256_text(value: str) -> str:
    """Return a SHA-256 digest without exposing the input."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
def sha256_bytes(value: bytes) -> str:
    """Return a SHA-256 digest for bytes."""
    return hashlib.sha256(value).hexdigest()
