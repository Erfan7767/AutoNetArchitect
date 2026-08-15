"""Authenticated encryption and hashing helpers."""
import base64, hashlib, hmac, secrets
from ..exceptions import SecurityError
def hash_secret(secret: str) -> str:
    """Hash a secret with a random salt using PBKDF2."""
    salt = secrets.token_bytes(16); digest = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, 200000); return base64.urlsafe_b64encode(salt + digest).decode()
def verify_secret(secret: str, encoded: str) -> bool:
    """Verify a PBKDF2 secret hash without revealing the secret."""
    try:
        raw = base64.urlsafe_b64decode(encoded.encode()); salt, expected = raw[:16], raw[16:]; actual = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, 200000); return hmac.compare_digest(actual, expected)
    except (ValueError, base64.binascii.Error): return False
def encrypt_text(plaintext: str, key: str) -> str:
    """Encrypt text with an authenticated XOR stream derived from a key."""
    if not key: raise SecurityError("encryption key is empty")
    nonce = secrets.token_bytes(16); stream = hashlib.sha256(key.encode() + nonce).digest(); data = bytes(c ^ stream[i % len(stream)] for i, c in enumerate(plaintext.encode())); tag = hmac.new(key.encode(), nonce + data, hashlib.sha256).digest()[:16]; return base64.urlsafe_b64encode(nonce + tag + data).decode()
def decrypt_text(ciphertext: str, key: str) -> str:
    """Authenticate and decrypt text."""
    try:
        raw = base64.urlsafe_b64decode(ciphertext.encode()); nonce, tag, data = raw[:16], raw[16:32], raw[32:];
        if not hmac.compare_digest(tag, hmac.new(key.encode(), nonce + data, hashlib.sha256).digest()[:16]): raise SecurityError("ciphertext authentication failed")
        stream = hashlib.sha256(key.encode() + nonce).digest(); return bytes(c ^ stream[i % len(stream)] for i, c in enumerate(data)).decode()
    except (ValueError, UnicodeDecodeError, base64.binascii.Error) as exc: raise SecurityError("ciphertext is invalid") from exc
