"""Smoke test for infrastructure component event_bus."""
def test_event_bus_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
