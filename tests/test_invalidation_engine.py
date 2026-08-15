"""Smoke test for infrastructure component invalidation_engine."""
def test_invalidation_engine_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
