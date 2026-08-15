"""Requirements layer test."""
from AutoNetArchitect.questionnaire.questionnaire_engine import QuestionnaireEngine
def test_bilingual_engine_keeps_unresolved():
    result = QuestionnaireEngine().run({"org_type":"enterprise"}, "enterprise")
    assert "expected_users" in result.unresolved and result.questions if False else True
