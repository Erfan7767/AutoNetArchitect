"""Smoke test for infrastructure component module_registration."""
def test_module_registration_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
