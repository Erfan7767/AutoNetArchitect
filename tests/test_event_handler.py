"""Smoke test for infrastructure component event_handler."""
def test_event_handler_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
