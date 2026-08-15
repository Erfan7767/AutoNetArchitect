"""Decision engine test."""
from decision_engine.confidence_governor import ConfidenceGovernor
def test_threshold():
    assert not ConfidenceGovernor().allow("deployment", .5)
