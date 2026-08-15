"""Tests for reusable pure UI components."""
from __future__ import annotations

from types import SimpleNamespace

from ui.components import ApprovalWidget, DeviceCard, LogViewer, ProgressTracker, TopologyViewer


def test_device_card_masks_sensitive_metadata():
    card = DeviceCard.from_mapping({"device_id": "edge-1", "vendor": "cisco", "platform": "ios_xe", "metadata": {"token": "raw", "credential_reference": "secret://vault/edge"}})
    rendered = card.render()
    assert rendered["metadata"]["token"] == "<REDACTED>"
    assert rendered["metadata"]["credential_reference"] == "secret://vault/edge"


def test_topology_viewer_preserves_evidence_and_fidelity():
    viewer = TopologyViewer.from_mapping({"nodes": [{"id": "a", "password": "raw"}], "links": [{"source": "a", "target": "b"}], "evidence_ids": ["e1"], "fidelity": "observed_partial"})
    rendered = viewer.render()
    assert rendered["evidence_ids"] == ["e1"]
    assert rendered["fidelity"] == "observed_partial"
    assert rendered["nodes"][0]["password"] == "<REDACTED>"


def test_progress_tracker_marks_current_and_completed_stages():
    context = SimpleNamespace(current_stage="design", completed_stages=("questionnaire", "requirements", "design"))
    rendered = ProgressTracker.from_context(context).render()
    design = next(item for item in rendered["stages"] if item["name"] == "design")
    assert design["current"] is True
    assert design["completed"] is True


def test_approval_widget_is_visible_but_non_executing():
    widget = ApprovalWidget.pending(action="deploy", stage="deployment_execution", reasons=("approval required",), required_role="change_approver")
    rendered = widget.render()
    assert rendered["status"] == "pending"
    assert rendered["approval_action"] == "external_governance_required"


def test_log_viewer_filters_and_marks_read_only():
    viewer = LogViewer.from_entries([{"event_type": "orchestrator.stage_transition", "outcome": "completed", "token": "raw"}, {"event_type": "other", "outcome": "blocked"}])
    rendered = viewer.filter(event_type="orchestrator.stage_transition").render()
    assert rendered["read_only"] is True
    assert len(rendered["entries"]) == 1
    assert rendered["entries"][0]["token"] == "<REDACTED>"
