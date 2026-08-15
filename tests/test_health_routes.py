"""Tests for health API routes."""
from __future__ import annotations

from tests.api_test_helpers import APITestHarness


def test_public_liveness_readiness_and_version():
    harness = APITestHarness()
    try:
        live = harness.client.get("/api/v1/health/live")
        ready = harness.client.get("/api/v1/health/ready")
        version = harness.client.get("/api/v1/health/version")
        assert live.status_code == 200
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"
        assert version.json()["api"] == "v1"
    finally:
        harness.close()


def test_audit_health_requires_audit_permission():
    harness = APITestHarness()
    try:
        assert harness.client.get("/api/v1/health/audit").status_code == 401
        response = harness.client.get("/api/v1/health/audit", headers=harness.auth_headers())
        assert response.status_code == 200
        assert response.json()["read_only"] is True
    finally:
        harness.close()
