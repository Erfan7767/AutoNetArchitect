"""Scope control test."""
from scope_control.safe_refusal import SafeRefusal
def test_refusal_fields():
    result = SafeRefusal().refuse("reason", "vendor", "design", "human review", True); assert result.violated_boundary == "vendor"
