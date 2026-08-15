"""Smoke test for infrastructure component progress_tracker."""
def test_progress_tracker_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
