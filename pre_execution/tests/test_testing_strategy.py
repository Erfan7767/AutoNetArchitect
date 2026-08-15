"""Pre-execution contract test."""
def test_testing_levels_exist():
    assert 'lab' in __import__('pathlib').Path('pre_execution/config/testing_strategy.yaml').read_text()
