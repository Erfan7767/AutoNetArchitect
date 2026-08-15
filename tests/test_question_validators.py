"""Requirements layer test."""
from AutoNetArchitect.questionnaire.questionnaire_engine import QuestionnaireEngine
def test_validator():
    assert QuestionnaireEngine().run({}, "enterprise").unresolved
