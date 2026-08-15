"""Foundation smoke test."""
def test_component_exists():
    from pathlib import Path
    assert Path(__file__).parents[1].exists()
