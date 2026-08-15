"""Chaos test for malformed API authentication responses."""
from __future__ import annotations

from api.server import encode_jwt
from tests.api_test_helpers import APITestHarness


def test_malformed_expiry_claim_is_rejected_as_authentication_failure():
    harness = APITestHarness()
    try:
        token = encode_jwt({"sub": "admin", "roles": ["admin"], "sid": "missing", "exp": "not-a-number", "scope": "local-single-user"}, harness.context.settings.jwt_secret)
        response = harness.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.status_code != 500
    finally:
        harness.close()
