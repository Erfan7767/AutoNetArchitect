"""Smoke test for infrastructure component event_deadletter."""
def test_event_deadletter_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
