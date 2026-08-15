from incident_response.auto_detection_rules import AutoDetectionRules, DetectionRule
from incident_response.incident_models import IncidentCategory, IncidentSeverity

def test_auto_detection_rules_match_threshold_without_containment():
    rules = AutoDetectionRules([DetectionRule(rule_id="r1", rule_name="high util", rule_type="threshold_rule", condition={"metric":"util", "operator":">", "threshold":95}, severity_assignment=IncidentSeverity.P3_MEDIUM, category=IncidentCategory.NETWORK_DEGRADATION, auto_create_incident=True)])
    result = rules.evaluate("r1", {"util":99})
    assert result.matched is True
    assert result.incident_creation_allowed is True

def test_auto_detection_rules_do_not_match_missing_signal():
    rule = DetectionRule(rule_id="r1", rule_name="state", rule_type="state_change_rule", condition={"field":"state", "state":"down"}, severity_assignment=IncidentSeverity.P1_CRITICAL, category=IncidentCategory.NETWORK_OUTAGE)
    assert AutoDetectionRules([rule]).evaluate("r1", {}).matched is False
