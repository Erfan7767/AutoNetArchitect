"""Decision engine test."""
from decision_engine.decision_context import DecisionContext, Objective, Alternative
from decision_engine.optimization_engine import OptimizationEngine
def test_no_decision_on_missing_evidence():
    context = DecisionContext("architecture", [Objective("cost", 1)], missing_information=["budget"])
    result = OptimizationEngine().decide(context, [Alternative("a", {"cost": 1}), Alternative("b", {"cost": 2})], confidence=0.9)
    assert result.status == "no_decision"
