"""Requirements layer test."""
from AutoNetArchitect.questionnaire.question_definitions import Question, LocalizedText
def test_question_bilingual():
    assert Question(question_id="x", text=LocalizedText(en="E", ar="ع"), field="x", value_type="text").text.ar == "ع"
