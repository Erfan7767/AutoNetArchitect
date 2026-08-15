"""Pre-execution contract test."""
def test_models_import():
    from pre_execution.foundation.pre_execution_models import ProjectState
    ProjectState('draft').validate()
