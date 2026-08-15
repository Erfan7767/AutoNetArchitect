"""Tests for project API routes."""
from __future__ import annotations

from tests.api_test_helpers import APITestHarness


def test_projects_require_authentication_and_support_local_crud():
    harness = APITestHarness()
    try:
        assert harness.client.get("/api/v1/projects").status_code == 401
        headers = harness.auth_headers()
        created = harness.client.post("/api/v1/projects", headers=headers, json={"name": "BankHQ", "sector": "banking", "description": "Core site"})
        assert created.status_code == 201, created.text
        listed = harness.client.get("/api/v1/projects", headers=headers)
        shown = harness.client.get("/api/v1/projects/BankHQ", headers=headers)
        assert listed.status_code == 200
        assert "BankHQ" in listed.json()["projects"]
        assert shown.status_code == 200
        assert shown.json()["persistence"]["checksum"]
        deleted = harness.client.delete("/api/v1/projects/BankHQ", headers=headers)
        assert deleted.status_code == 204
    finally:
        harness.close()


def test_viewer_cannot_create_project():
    harness = APITestHarness()
    try:
        response = harness.client.post("/api/v1/projects", headers=harness.auth_headers("viewer", "viewer-password-123"), json={"name": "Blocked"})
        assert response.status_code == 403
    finally:
        harness.close()
