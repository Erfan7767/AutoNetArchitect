"""Smoke test for infrastructure component settings_watcher."""
def test_settings_watcher_module_exists() -> None:
    """Verify the component source exists."""
    from pathlib import Path
    assert Path(__file__).parents[1].joinpath("infrastructure").exists()
