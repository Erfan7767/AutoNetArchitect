"""Requirements layer test."""
from AutoNetArchitect.questionnaire.constraint_rules import ConstraintRules
def test_wan_rule():
    assert ConstraintRules().evaluate({"wan_required":True,"site_count":1})
