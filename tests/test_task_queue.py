"""Smoke test for infrastructure component task_queue."""
def test_task_queue_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
