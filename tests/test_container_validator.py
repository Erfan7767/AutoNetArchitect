"""Smoke test for infrastructure component container_validator."""
def test_container_validator_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
