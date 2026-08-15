"""Requirements layer test."""
from AutoNetArchitect.requirements.formulas import FormulaRegistry
def test_formula_provenance():
    assert FormulaRegistry().evaluate("user_capacity", users=100)["source"]
