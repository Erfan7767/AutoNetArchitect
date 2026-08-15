"""Pre-execution contract test."""
def test_state_machine_has_deployed():
    assert 'deployed' in __import__('pathlib').Path('pre_execution/config/project_state_machine.json').read_text()
