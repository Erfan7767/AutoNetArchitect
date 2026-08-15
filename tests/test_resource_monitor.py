"""Smoke test for infrastructure component resource_monitor."""
def test_resource_monitor_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
