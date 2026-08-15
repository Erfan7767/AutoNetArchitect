"""Pre-execution contract test."""
def test_product_scope_config_exists():
    assert __import__('pathlib').Path('pre_execution/config/product_scope.yaml').exists()
