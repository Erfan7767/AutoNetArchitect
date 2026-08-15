"""Pre-execution contract test."""
def test_approval_required():
    import pytest
    from pre_execution.foundation.dependency_policy import require_approval
    with pytest.raises(Exception): require_approval('deployment')
