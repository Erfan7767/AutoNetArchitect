"""Bilingual questionnaire orchestration."""
from __future__ import annotations
from typing import Any
from .question_definitions import Question, QuestionAnswer, LocalizedText
from .validators import QuestionnaireValidators, ValidationIssue
from .contradiction_detector import ContradictionDetector, ContradictionReport
from .defaults_engine import DefaultsEngine
from .scoring import ScoringEngine
class QuestionnaireResult:
    """Complete questionnaire result."""
    def __init__(self, answers: dict[str, Any], unresolved: list[str], issues: list[ValidationIssue], contradictions: ContradictionReport, score: float, defaults: dict[str, dict[str, Any]]) -> None:
        self.answers, self.unresolved, self.issues, self.contradictions, self.score, self.defaults = answers, unresolved, issues, contradictions, score, defaults
class QuestionnaireEngine:
    """Run bilingual questions without hiding unresolved mandatory facts."""
    def __init__(self, questions: list[Question] | None = None) -> None:
        self.questions = questions or self.default_questions(); self.validators = QuestionnaireValidators(); self.detector = ContradictionDetector(); self.defaults = DefaultsEngine(); self.scoring = ScoringEngine()
    @staticmethod
    def default_questions() -> list[Question]:
        """Return baseline bilingual questions."""
        return [Question(question_id="org_type", text=LocalizedText(en="Organization type", ar="نوع المنظمة"), field="org_type", value_type="choice", mandatory_for=["all"], choices=["enterprise", "sme", "government", "education"]), Question(question_id="environment", text=LocalizedText(en="Environment type", ar="نوع البيئة"), field="environment_type", value_type="choice", mandatory_for=["all"], choices=["brownfield", "greenfield"]), Question(question_id="users", text=LocalizedText(en="Expected users", ar="عدد المستخدمين المتوقع"), field="expected_users", value_type="integer", human_supplied_mandatory=True), Question(question_id="sites", text=LocalizedText(en="Site count", ar="عدد المواقع"), field="site_count", value_type="integer", human_supplied_mandatory=True)]
    def run(self, answers: dict[str, Any], org_type: str) -> QuestionnaireResult:
        """Validate, detect contradictions, score, and suggest defaults."""
        issues = self.validators.validate(self.questions, answers, org_type); unresolved = [issue.field for issue in issues if "unresolved" in issue.message_en]; contradictions = self.detector.detect(answers); required = [q.field for q in self.questions if org_type in q.mandatory_for or q.human_supplied_mandatory]; score = self.scoring.score(required, answers, len(contradictions.contradictions)); return QuestionnaireResult(answers, unresolved, issues, contradictions, score, self.defaults.suggest(answers))
