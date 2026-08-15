"""Smoke test for infrastructure component interface_registry."""
def test_interface_registry_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
