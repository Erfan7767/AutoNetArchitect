"""Foundation smoke test."""
from AutoNetArchitect.utils.crypto_utils import encrypt_text, decrypt_text
def test_roundtrip():
    assert decrypt_text(encrypt_text("safe", "key"), "key") == "safe"
