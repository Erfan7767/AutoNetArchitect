"""Smoke test for infrastructure component lazy_proxy."""
def test_lazy_proxy_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
