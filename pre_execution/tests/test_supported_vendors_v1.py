"""Pre-execution contract test."""
def test_huawei_supported():
    from pre_execution.foundation.dependency_policy import validate_vendor
    assert validate_vendor('Huawei') == 'Huawei'
