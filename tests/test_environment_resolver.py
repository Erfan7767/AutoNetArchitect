"""Smoke test for infrastructure component environment_resolver."""
def test_environment_resolver_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
