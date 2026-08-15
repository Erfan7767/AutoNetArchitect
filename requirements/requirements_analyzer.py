"""Requirements document construction."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field
from questionnaire.questionnaire_engine import QuestionnaireEngine
from questionnaire.question_definitions import Question
from .formulas import FormulaRegistry
from .scaling_engine import ScalingEngine
from .capacity_planner import CapacityPlanner
from .industry_standards import IndustryStandards
class RequirementsDocument(BaseModel):
    """Complete auditable requirements analysis output."""
    organization_type: str
    environment_type: str
    answers: dict[str, Any]
    normalized_requirements: dict[str, Any]
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_human_supplied_mandatory: list[str] = Field(default_factory=list)
    contradictions: list[dict[str, Any]] = Field(default_factory=list)
    formulas: dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.0
class RequirementsAnalyzer:
    """Analyze questionnaire answers into a complete requirements document."""
    def __init__(self, questions: list[Question] | None = None) -> None: self.questionnaire = QuestionnaireEngine(questions); self.formulas = FormulaRegistry(); self.scaling = ScalingEngine(); self.capacity = CapacityPlanner(self.scaling); self.standards = IndustryStandards()
    def analyze(self, answers: dict[str, Any], org_type: str) -> RequirementsDocument:
        """Build a document and explicitly preserve unresolved mandatory inputs."""
        result = self.questionnaire.run(answers, org_type); environment = self.scaling.classify_environment(answers); users = int(answers.get("expected_users") or 0); growth = float(answers.get("annual_growth") or 0.2); normalized = {**answers, "environment_type": environment, "capacity": self.capacity.plan(users, growth)}; assumptions = [{"field": k, **v} for k, v in result.defaults.items() if k not in answers]; decisions = [{"decision_id": "REQ-ENV", "decision": environment, "source": "derived_from_answers"}]; formulas = {"user_capacity": self.formulas.evaluate("user_capacity", users=users, growth=growth)}; return RequirementsDocument(organization_type=org_type, environment_type=environment, answers=answers, normalized_requirements=normalized, decisions=decisions, assumptions=assumptions, unresolved_human_supplied_mandatory=result.unresolved, contradictions=[v.__dict__ for v in result.contradictions.contradictions], formulas=formulas, confidence_score=result.score)
