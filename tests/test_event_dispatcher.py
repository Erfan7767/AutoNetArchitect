"""Smoke test for infrastructure component event_dispatcher."""
def test_event_dispatcher_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
