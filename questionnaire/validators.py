"""Answer and mandatory-field validation."""
from __future__ import annotations
from typing import Any
from .question_definitions import Question
class ValidationIssue:
    """Validation issue with bilingual message."""
    def __init__(self, field: str, message_en: str, message_ar: str) -> None: self.field, self.message_en, self.message_ar = field, message_en, message_ar
class QuestionnaireValidators:
    """Validate types, choices, and human-supplied mandatory values."""
    def validate(self, questions: list[Question], answers: dict[str, Any], org_type: str) -> list[ValidationIssue]:
        """Return validation issues without silently filling mandatory facts."""
        issues: list[ValidationIssue] = []
        for q in questions:
            value = answers.get(q.field)
            mandatory = org_type in q.mandatory_for or q.human_supplied_mandatory
            if mandatory and value in (None, ""): issues.append(ValidationIssue(q.field, "Required human input is unresolved", "المدخل البشري الإلزامي غير محسوم"))
            if q.choices and value not in (None, "") and value not in q.choices: issues.append(ValidationIssue(q.field, "Value is not an allowed choice", "القيمة ليست من الخيارات المسموحة"))
        return issues
