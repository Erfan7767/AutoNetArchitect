"""Tests for the FastAPI server foundation."""
from __future__ import annotations

from tests.api_test_helpers import APITestHarness


def test_api_root_and_versioned_metadata():
    harness = APITestHarness()
    try:
        root = harness.client.get("/")
        version = harness.client.get("/api/v1/health/version")
        assert root.status_code == 200
        assert root.json()["multi_tenant"] is False
        assert version.status_code == 200
        assert version.json()["api"] == "v1"
    finally:
        harness.close()


def test_api_docs_and_openapi_are_exposed():
    harness = APITestHarness()
    try:
        assert harness.client.get("/docs").status_code == 200
        schema = harness.client.get("/openapi.json")
        assert schema.status_code == 200
        assert "/api/v1/projects" in schema.json()["paths"]
    finally:
        harness.close()
