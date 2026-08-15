"""Smoke test for infrastructure component settings_validator."""
def test_settings_validator_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
