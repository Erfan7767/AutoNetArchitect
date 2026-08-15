"""Tests for authentication API routes."""
from __future__ import annotations

from tests.api_test_helpers import APITestHarness


def test_login_me_and_logout_revoke_session():
    harness = APITestHarness()
    try:
        bad = harness.client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong-password"})
        assert bad.status_code in {401, 422}
        token = harness.login()
        headers = {"Authorization": f"Bearer {token}"}
        me = harness.client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["username"] == "admin"
        assert "password" not in me.text.lower()
        logged_out = harness.client.post("/api/v1/auth/logout", headers=headers)
        assert logged_out.status_code == 204
        revoked = harness.client.get("/api/v1/auth/me", headers=headers)
        assert revoked.status_code == 401
    finally:
        harness.close()


def test_login_response_contains_bearer_jwt_metadata_only():
    harness = APITestHarness()
    try:
        response = harness.client.post("/api/v1/auth/login", json={"username": "admin", "password": "strong-password-123"})
        body = response.json()
        assert response.status_code == 200
        assert body["token_type"] == "bearer"
        assert body["access_token"].count(".") == 2
        assert "strong-password" not in response.text
    finally:
        harness.close()
