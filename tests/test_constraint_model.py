"""Decision engine test."""
from decision_engine.constraint_model import Constraint
from decision_engine.decision_context import Alternative
def test_hard_constraint():
    assert not Constraint("x", "hard", lambda a: False).evaluate(Alternative("a")).satisfied
