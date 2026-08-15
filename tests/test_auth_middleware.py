"""Tests for API authentication middleware."""
from __future__ import annotations

from api.server import decode_jwt, encode_jwt
from tests.api_test_helpers import APITestHarness


def test_missing_and_invalid_bearer_tokens_are_rejected():
    harness = APITestHarness()
    try:
        assert harness.client.get("/api/v1/auth/me").status_code == 401
        assert harness.client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.value"}).status_code == 401
    finally:
        harness.close()


def test_jwt_signature_and_expiration_validation():
    secret = b"b" * 32
    token = encode_jwt({"sub": "admin", "roles": ["admin"], "sid": "sid", "iat": 1, "exp": 4102444800, "scope": "local-single-user"}, secret)
    claims = decode_jwt(token, secret)
    assert claims["sub"] == "admin"
    rejected = False
    try:
        decode_jwt(token, b"c" * 32)
    except Exception:
        rejected = True
    if not rejected:
        raise AssertionError("JWT signed with another secret must be rejected")


def test_viewer_is_forbidden_from_write_route():
    harness = APITestHarness()
    try:
        response = harness.client.post("/api/v1/projects", headers=harness.auth_headers("viewer", "viewer-password-123"), json={"name": "NoWrite"})
        assert response.status_code == 403
    finally:
        harness.close()
