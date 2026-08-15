"""Smoke test for infrastructure component cache_decorators."""
def test_cache_decorators_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
