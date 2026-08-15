from digital_twin import StateCertainty, TransientStateClassifier


def test_transient_classifier_marks_changed_unstable_state_as_inferred():
    result = TransientStateClassifier().classify("edge-1", {"state": "up"}, {"state": "down"}, stability_observations=1, required_stability_observations=2, observed_at="2026-01-02", evidence_ids=["t-1"])
    assert result.label == "transient_change"
    assert result.state_kind == "inferred_transient_state"
    assert result.certainty == StateCertainty.INFERRED.value


def test_transient_classifier_marks_stable_and_missing_states_distinctly():
    stable = TransientStateClassifier().classify("edge-1", {"state": "down"}, {"state": "down"}, stability_observations=2, required_stability_observations=2, evidence_ids=["t-2"])
    assert stable.label == "stable_observed"
    assert stable.certainty == StateCertainty.OBSERVED.value
    unknown = TransientStateClassifier().classify("edge-1", None, None)
    assert unknown.label == "unknown"
    assert unknown.certainty == StateCertainty.UNKNOWN.value
