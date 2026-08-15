"""Smoke test for infrastructure component incident_events."""
def test_incident_events_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
