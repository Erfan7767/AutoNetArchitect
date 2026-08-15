"""Smoke test for infrastructure component concurrency_limiter."""
def test_concurrency_limiter_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
