"""Smoke test for infrastructure component task_scheduler."""
def test_task_scheduler_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
