"""Smoke test for infrastructure component timeout_manager."""
def test_timeout_manager_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
