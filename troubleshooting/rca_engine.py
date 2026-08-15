"""Evidence-bounded root cause analysis for troubleshooting results."""

from __future__ import annotations

from typing import Iterable

from designers.base_designer import Assumption, DecisionRecord

from .models import EvidenceCollection, Hypothesis, HypothesisEvaluation, RootCauseAnalysis, RootCauseClassification


class RCAEngine:
    """Select a likely root cause only when evidence supports the selection."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def analyze(self, hypotheses: Iterable[Hypothesis], evaluations: Iterable[HypothesisEvaluation], evidence: EvidenceCollection, *, known_issue_matches: Iterable[object] = ()) -> RootCauseAnalysis:
        """Produce RCA with explicit supporting, contradicting, and unresolved evidence."""
        hypothesis_list = list(hypotheses)
        evaluation_list = list(evaluations)
        evidence_by_id = evidence.by_id()
        ordered = sorted(evaluation_list, key=lambda item: (item.status == "supported", item.confidence, item.support_score), reverse=True)
        selected = ordered[0] if ordered and ordered[0].status == "supported" else None
        if selected is None:
            root_cause = "insufficient evidence to determine a single root cause"
            confidence = max((item.confidence for item in evaluation_list), default=0.1)
            classification = RootCauseClassification.UNKNOWN
            unresolved = list(dict.fromkeys(evidence.missing_required + ["no hypothesis achieved supported status"]))
        else:
            hypothesis = next((item for item in hypothesis_list if item.hypothesis_id == selected.hypothesis_id), None)
            root_cause = hypothesis.description if hypothesis else selected.hypothesis_id
            confidence = min(0.95, selected.confidence)
            classification = self._classify(hypothesis.affects_layer if hypothesis else "")
            unresolved = list(selected.missing_evidence)
            if len([item for item in ordered if item.status == "supported" and abs(item.confidence - selected.confidence) < 0.1]) > 1:
                unresolved.append("multiple hypotheses have comparable support")
                confidence = min(confidence, 0.7)
        level = "high" if confidence > 0.8 else "medium" if confidence >= 0.5 else "low" if confidence >= 0.3 else "inconclusive"
        if confidence < 0.3:
            self.assumptions.append(Assumption("root_cause", "unknown", "available evidence does not support a reliable cause selection", True))
        supporting = [evidence_by_id[item] for item in (selected.supporting_evidence_ids if selected else []) if item in evidence_by_id]
        contradicting = [evidence_by_id[item] for item in (selected.contradicting_evidence_ids if selected else []) if item in evidence_by_id]
        decision = DecisionRecord("RCAEngine", "root-cause-analysis", root_cause, "select a supported hypothesis only when its evidence score exceeds the bounded threshold", ["supported_hypothesis", "unknown_insufficient_evidence"], {"supported_hypothesis": "selected only with explicit support", "unknown_insufficient_evidence": "selected when support is insufficient"})
        self.decisions.append(decision)
        return RootCauseAnalysis(root_cause=root_cause, root_cause_confidence=round(confidence, 3), contributing_factors=["recent changes or known issues require separate evidence confirmation"] if known_issue_matches else [], evidence_supporting=supporting, evidence_contradicting=contradicting, root_cause_classification=classification, confidence_level=level, unresolved_uncertainties=list(dict.fromkeys(unresolved)), tested_hypotheses=evaluation_list)

    @staticmethod
    def _classify(layer: str) -> RootCauseClassification:
        """Map affected layer to a conservative cause category."""
        normalized = layer.lower()
        if "physical" in normalized or normalized == "l1":
            return RootCauseClassification.HARDWARE_FAILURE
        if "security" in normalized or "acl" in normalized:
            return RootCauseClassification.SECURITY_INCIDENT
        if "design" in normalized:
            return RootCauseClassification.DESIGN_FLAW
        if "l2" in normalized or "l3" in normalized or "l4" in normalized or "config" in normalized:
            return RootCauseClassification.CONFIGURATION_ERROR
        return RootCauseClassification.UNKNOWN
