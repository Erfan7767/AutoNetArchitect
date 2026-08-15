"""Tests for inter-phase validation."""
from execution_protocol.inter_phase_validator import InterPhaseValidator

def test_validator_report_has_core_sections() -> None:
    """A validation report exposes all required result categories."""
    report = InterPhaseValidator().validate([], [])
    assert {'syntax_errors', 'missing_symbols', 'signature_changes'} <= set(report)
