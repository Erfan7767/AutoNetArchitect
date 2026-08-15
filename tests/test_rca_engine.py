from troubleshooting.hypothesis_engine import HypothesisEngine
from troubleshooting.models import EvidenceCollection, EvidenceItem, SymptomClassification, SymptomClass, CollectionMethod, EvidenceSource
from troubleshooting.rca_engine import RCAEngine


def test_rca_engine_selects_supported_hypothesis_with_bounded_confidence():
    classification = SymptomClassification(primary_class=SymptomClass.CONNECTIVITY_LOSS, subtype="total", confidence=0.8, rationale="test", suggested_diagnostic_workflows=["connectivity_diagnostic"], decision_id="d")
    engine = HypothesisEngine()
    hypotheses = engine.generate(classification)
    evidence = EvidenceCollection(items=[EvidenceItem(evidence_id="ev-1", source=EvidenceSource.PARSED_OUTPUT, raw_data="interface down error", parsed_data={"state":"down"}, collection_method=CollectionMethod.PARSED, confidence=0.9)], mode="parsed_output", complete=True)
    evaluations = [engine.evaluate(item, evidence) for item in hypotheses[:2]]
    rca = RCAEngine().analyze(hypotheses, evaluations, evidence)
    assert 0.0 <= rca.root_cause_confidence <= 1.0
    assert rca.root_cause


def test_rca_engine_returns_unknown_with_no_evidence():
    classification = SymptomClassification(primary_class=SymptomClass.CONNECTIVITY_LOSS, subtype="total", confidence=0.8, rationale="test", suggested_diagnostic_workflows=["connectivity_diagnostic"], decision_id="d")
    engine = HypothesisEngine()
    hypotheses = engine.generate(classification)
    empty = EvidenceCollection(mode="offline", complete=False, missing_required=["interface_state"])
    rca = RCAEngine().analyze(hypotheses, [], empty)
    assert rca.root_cause_classification.value == "unknown"
    assert rca.root_cause_confidence < 0.3
