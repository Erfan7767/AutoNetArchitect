"""Knowledge lifecycle test."""
from knowledge_lifecycle.formula_lifecycle import FormulaLifecycle, FormulaVersion
def test_formula_deprecation():
    lifecycle = FormulaLifecycle(); lifecycle.register(FormulaVersion("f", "1", "source", "x")); lifecycle.deprecate("f", "1", "changed"); assert not lifecycle.active("f")
