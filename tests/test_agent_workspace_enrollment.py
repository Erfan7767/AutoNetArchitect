"""Tests for secret-free, durable local enrollment receipt persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from site_agent.enrollment import EnrollmentReceipt
from windows_app.workspace import WindowsWorkspace


def test_workspace_persists_only_the_secret_free_enrollment_receipt(tmp_path) -> None:
    """The Windows workspace round-trips enrollment identity and never records a private key."""

    receipt = EnrollmentReceipt(
        enrollment_id="enrollment-workspace-001",
        agent_id="agent-workspace-001",
        site_id="site-workspace-001",
        scope_hash="a" * 64,
        agent_fingerprint="b" * 64,
        control_plane_fingerprint="c" * 64,
        enrolled_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
    )
    workspace = WindowsWorkspace(tmp_path / "workspace")

    saved = workspace.save_enrollment_receipt(receipt)
    loaded = workspace.load_enrollment_receipt()
    persisted = (tmp_path / "workspace" / "agent_enrollment_receipt.json").read_text(encoding="utf-8")

    assert saved == receipt
    assert loaded == receipt
    assert "private" not in persisted.lower()
    assert "credential" not in persisted.lower()
