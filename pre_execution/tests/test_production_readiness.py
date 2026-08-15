"""Pre-execution contract test."""
def test_readiness_requires_rollback():
    assert 'rollback' in __import__('pathlib').Path('pre_execution/config/production_readiness.yaml').read_text()
