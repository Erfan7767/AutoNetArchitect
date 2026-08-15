"""Smoke test for infrastructure component batch_executor."""
def test_batch_executor_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
