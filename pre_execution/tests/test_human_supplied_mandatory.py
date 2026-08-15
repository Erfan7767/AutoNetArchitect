"""Pre-execution contract test."""
def test_human_field_validates():
    from pre_execution.foundation.pre_execution_models import HumanSuppliedMandatory
    HumanSuppliedMandatory('topology').validate()
