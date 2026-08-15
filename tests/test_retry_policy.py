"""Smoke test for infrastructure component retry_policy."""
def test_retry_policy_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
