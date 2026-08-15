from troubleshooting.hypothesis_engine import HypothesisEngine
from troubleshooting.models import EvidenceCollection, EvidenceItem, SymptomClassification, SymptomClass, CollectionMethod, EvidenceSource


def test_hypothesis_engine_generates_ordered_hypotheses():
    classification = SymptomClassification(primary_class=SymptomClass.CONNECTIVITY_LOSS, subtype="total", confidence=0.8, rationale="test", suggested_diagnostic_workflows=["connectivity_diagnostic"], decision_id="d-1")
    hypotheses = HypothesisEngine().generate(classification)
    assert len(hypotheses) >= 5
    assert hypotheses[0].probability_score >= hypotheses[-1].probability_score
    assert all(step.read_only for item in hypotheses for step in item.verification_steps)


def test_hypothesis_engine_evaluates_supporting_evidence():
    engine = HypothesisEngine()
    classification = SymptomClassification(primary_class=SymptomClass.CONNECTIVITY_LOSS, subtype="total", confidence=0.8, rationale="test", suggested_diagnostic_workflows=["connectivity_diagnostic"], decision_id="d-2")
    hypothesis = engine.generate(classification)[0]
    evidence = EvidenceCollection(items=[EvidenceItem(evidence_id="ev-1", source=EvidenceSource.PARSED_OUTPUT, raw_data="interface down crc error", parsed_data={"state":"down"}, collection_method=CollectionMethod.PARSED, confidence=0.9)], mode="parsed_output", complete=True)
    evaluation = engine.evaluate(hypothesis, evidence)
    assert 0.0 <= evaluation.confidence <= 1.0
    assert evaluation.hypothesis_id == hypothesis.hypothesis_id
