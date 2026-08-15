"""Foundation smoke test."""
from AutoNetArchitect.models.decisions import DecisionRecord
def test_decision_conversion():
    item = DecisionRecord(decision_id="ADR-1", title="t", context="c", decision="d"); assert item.to_dict()["schema_version"]
