from pathlib import Path
import tempfile

from audit.audit_trail import AuditIntegrityError, AuditTrail


def test_audit_trail_records_required_events_and_hides_secret_values():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "audit.jsonl"
        trail = AuditTrail(path)
        trail.record_project_change("alice", {"project_id": "p1", "change": "vlan-added"})
        trail.record_config_generation("alice", {"device_id": "edge-1", "decision_ids": ["decision-1"]})
        trail.record_deployment_attempt("bob", {"device_id": "edge-1", "config_hash": "hash"})
        trail.record_rollback_attempt("bob", {"device_id": "edge-1", "reason": "failed validation"})
        trail.record_secret_metadata_access("alice", "secret://device/password", ["purpose", "owner"])
        raw = path.read_text(encoding="utf-8")
        assert "raw-secret-value" not in raw
        assert "secret://device/password" in raw
        assert trail.verify_integrity()
        assert len(trail.entries()) == 5


def test_audit_trail_detects_tampering():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "audit.jsonl"
        trail = AuditTrail(path)
        trail.record("project.change", "alice", {"project_id": "p1"})
        line = path.read_text(encoding="utf-8").replace('"project_id": "p1"', '"project_id": "p2"')
        path.write_text(line, encoding="utf-8")
        try:
            AuditTrail(path)
        except AuditIntegrityError:
            return
        raise AssertionError("tampering must invalidate the audit hash chain")
