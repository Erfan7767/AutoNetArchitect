"""Pre-execution contract test."""
def test_runtime_mode_is_single_user():
    assert 'single_user' in __import__('pathlib').Path('pre_execution/config/runtime_mode.yaml').read_text()
