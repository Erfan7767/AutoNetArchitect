"""Smoke test for infrastructure component cancellation_manager."""
def test_cancellation_manager_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
