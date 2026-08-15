from datetime import datetime, timezone
import tempfile

from operations import DriftDetector, DriftSeverity, MonitoringObservation, MonitoringSnapshot
from source_of_truth.sot_manager import SoTManager, SoTType


def _sot():
    store = SoTManager(tempfile.mktemp(suffix=".json"))
    record = store.register(SoTType.OPERATIONAL, {"operational_state": {"targets": {"edge-1": {"routing": {"state": "up"}, "ntp": "synchronized"}}}}, "operations-owner", "approved-operational-source", ("ev-sot",), approved=False)
    return store.approve(record.record_id, "operations-owner")


def _snapshot(values):
    observation = MonitoringObservation("CYCLE-1:edge-1", "edge-1", datetime.now(timezone.utc).isoformat(), "observed", values, ("ev-observed",))
    return MonitoringSnapshot("CYCLE-1", observation.observed_at, (observation,), True, ("ev-cycle",))


def test_drift_detector_compares_only_approved_operational_sot_and_blocks_high_risk_drift():
    report = DriftDetector().compare("DRIFT-1", _snapshot({"routing": {"state": "down"}, "ntp": "synchronized"}), _sot())
    assert report.read_only is True
    assert report.severity == DriftSeverity.HIGH.value
    assert report.production_gate == "block_or_review"
    assert report.remediation_allowed is False
    assert any(item.path == "routing.state" for item in report.items)


def test_drift_detector_reports_no_drift_when_observation_matches_sot():
    report = DriftDetector().compare("DRIFT-2", _snapshot({"routing": {"state": "up"}, "ntp": "synchronized"}), _sot())
    assert report.severity == DriftSeverity.NONE.value
    assert report.production_gate == "allow"
    assert report.items == ()


def test_drift_detector_rejects_unapproved_or_wrong_sot_type():
    store = SoTManager(tempfile.mktemp(suffix=".json"))
    record = store.register(SoTType.DESIGN, {"targets": {"edge-1": {"state": "up"}}}, "design-owner", "design-source")
    try:
        DriftDetector().compare("DRIFT-3", _snapshot({"state": "up"}), record)
    except ValueError as error:
        assert "approved OPERATIONAL_SOT" in str(error)
    else:
        raise AssertionError("wrong SoT type must be rejected")
