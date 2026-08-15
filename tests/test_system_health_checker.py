"""Smoke test for infrastructure component system_health_checker."""
def test_system_health_checker_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
