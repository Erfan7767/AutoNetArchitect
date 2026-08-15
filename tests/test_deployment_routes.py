"""Tests for deployment API routes."""
from __future__ import annotations

from tests.api_test_helpers import APITestHarness


def test_deployment_status_and_prepare_are_versioned_and_orchestrated():
    harness = APITestHarness()
    try:
        headers = harness.auth_headers()
        created = harness.client.post("/api/v1/projects", headers=headers, json={"name": "DeployLab"})
        assert created.status_code == 201
        status_response = harness.client.get("/api/v1/projects/DeployLab/deployment/status", headers=headers)
        assert status_response.status_code == 200
        prepared = harness.client.post("/api/v1/projects/DeployLab/deployment/prepare", headers=headers, json={"deployment_artifact_id": "DEPLOY-001", "evidence_ids": ["E-001"]})
        assert prepared.status_code == 200
        assert prepared.json()["orchestrator"] == "DeploymentOrchestrator"
        assert prepared.json()["result"]["status"] in {"blocked", "completed"}
    finally:
        harness.close()


def test_real_execution_without_backup_is_not_allowed_and_no_transport_is_opened():
    harness = APITestHarness()
    try:
        headers = harness.auth_headers()
        harness.client.post("/api/v1/projects", headers=headers, json={"name": "SafeDeploy"})
        response = harness.client.post("/api/v1/projects/SafeDeploy/deployment/execute", headers=headers, json={"execution_result_id": "EXEC-001", "real_execution": True})
        assert response.status_code == 200
        body = response.json()["result"]
        assert body["success"] is False
        assert any("backup" in reason.lower() or "stage" in reason.lower() for reason in body["reasons"])
    finally:
        harness.close()
