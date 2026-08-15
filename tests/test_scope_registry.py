"""Scope control test."""
from scope_control.scope_registry import ScopeRegistry
def test_workflow_boundary():
    result = ScopeRegistry().check("design", {"vendor":"Cisco"}); assert not result.allowed and result.violations[0]["status"] == "unsupported"
