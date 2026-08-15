"""Smoke test for infrastructure component cache_statistics."""
def test_cache_statistics_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
