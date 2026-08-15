from pathlib import Path
import tempfile

from audit.audit_reporter import AuditReporter
from audit.audit_trail import AuditTrail


def test_audit_reporter_generates_aggregates_and_json_report():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        trail = AuditTrail(root / "audit.jsonl")
        trail.record_project_change("alice", {"project_id": "p1"})
        trail.record_config_generation("alice", {"device_id": "edge-1"})
        trail.record_deployment_attempt("bob", {"device_id": "edge-1"}, outcome="blocked")
        reporter = AuditReporter(trail)
        report = reporter.generate()
        assert report.total_entries == 3
        assert report.by_actor["alice"] == 2
        assert report.by_event_type["deployment.attempt"] == 1
        output = report.write_json(root / "report.json")
        assert output.exists()
        assert "edge-1" in output.read_text(encoding="utf-8")


def test_audit_reporter_filters_entries():
    with tempfile.TemporaryDirectory() as directory:
        trail = AuditTrail(Path(directory) / "audit.jsonl")
        trail.record_project_change("alice", {"project_id": "p1"})
        trail.record_project_change("bob", {"project_id": "p2"})
        report = AuditReporter(trail).generate(actor="alice")
        assert report.total_entries == 1
        assert report.entries[0].actor == "alice"
