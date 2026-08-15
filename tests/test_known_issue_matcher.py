from troubleshooting.known_issue_matcher import KnownIssueMatcher
from troubleshooting.models import SymptomClassification, SymptomClass


def test_known_issue_matcher_requires_scope_and_matches_pattern():
    classification = SymptomClassification(primary_class=SymptomClass.ROUTING_ISSUE, subtype="unreachable", confidence=0.8, rationale="test", suggested_diagnostic_workflows=["routing_diagnostic"], matched_terms=["ospf"], decision_id="d")
    matches = KnownIssueMatcher().match(classification, [{"issue_id":"i1", "vendor":"cisco", "platform":"ios_xe", "affected_versions":["17.9"], "symptom_patterns":["ospf"], "root_cause":"mtu"}], vendor="cisco", platform="ios_xe", version="17.9")
    assert matches
    assert matches[0].confidence <= 1.0


def test_known_issue_matcher_does_not_match_incompatible_vendor():
    classification = SymptomClassification(primary_class=SymptomClass.ROUTING_ISSUE, subtype="unreachable", confidence=0.8, rationale="test", suggested_diagnostic_workflows=["routing_diagnostic"], matched_terms=["ospf"], decision_id="d")
    assert KnownIssueMatcher().match(classification, [{"issue_id":"i1", "vendor":"juniper", "platform":"junos", "symptom_patterns":["ospf"]}], vendor="cisco") == []
