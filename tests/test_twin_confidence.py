from digital_twin import StateIngestor, TwinConfidenceEvaluator, TwinModel


def test_twin_confidence_reports_evidence_bounded_score_and_missing_views():
    ingestor = StateIngestor()
    logical = ingestor.ingest("edge-1", "logical", {"role": "core"}, source="design", evidence_ids=("d-1",), confidence=0.9)
    inferred = ingestor.ingest("edge-1", "inferred", {"state": "transition"}, source="estimator", evidence_ids=("i-1",), certainty="inferred", confidence=0.5)
    report = TwinConfidenceEvaluator().evaluate(TwinModel("twin-1", "2026-01-01").add_state(logical).add_state(inferred))
    assert report.level in {"low", "medium"}
    assert "deployment_state" in report.missing_state_kinds
    assert report.inferred_state_count == 1
    assert report.production_safe_claim_allowed is False
    assert report.full_fidelity_claim is False
    assert report.fidelity_cap == "evidence_bounded"


def test_twin_confidence_accepts_explicit_full_fidelity_evidence_only_when_supplied():
    ingestor = StateIngestor()
    state = ingestor.ingest("edge-1", "logical", {"role": "core"}, source="design", evidence_ids=("d-1",), confidence=0.9)
    report = TwinConfidenceEvaluator().evaluate(TwinModel("twin-1", "2026-01-01").add_state(state), protocol_fidelity_evidence={"full_fidelity": True, "evidence_ids": ["protocol-lab-1"]})
    assert report.full_fidelity_claim is True
    assert report.fidelity_cap == "full_fidelity_evidenced"
    assert report.production_safe_claim_allowed is False
