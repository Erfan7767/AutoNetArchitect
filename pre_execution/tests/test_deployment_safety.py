"""Pre-execution contract test."""
def test_deployment_policy_exists():
    assert __import__('pathlib').Path('pre_execution/config/deployment_safety_policy.json').exists()
