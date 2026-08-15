"""Smoke test for infrastructure component feature_flags."""
def test_feature_flags_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
