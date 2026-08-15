"""Physical execution feasibility checker."""
from __future__ import annotations
from dataclasses import dataclass, field
from .site_survey_requirements import SiteSurveyRequirements
@dataclass
class FeasibilityResult:
    """Distinguish logical feasibility from field execution feasibility."""
    status: str
    logical_feasible: bool
    field_feasible: bool
    reasons: list[str] = field(default_factory=list)
    survey_requirements: list[str] = field(default_factory=list)
    physical_recommendation_allowed: bool = False
class FieldFeasibilityChecker:
    """Check rack, feeds, pathways, redundancy, access, and safety before recommendation."""
    def __init__(self, survey: SiteSurveyRequirements | None = None) -> None: self.survey = survey or SiteSurveyRequirements()
    def check(self, site: object, logical_feasible: bool, proposed_rack_units: int = 0, proposed_feeds: int = 0, require_redundancy: bool = False) -> FeasibilityResult:
        """Return a guarded feasibility state with no invented physical values."""
        reasons: list[str] = []; missing = self.survey.required_for(site, proposed_rack_units, proposed_feeds)
        if not logical_feasible: reasons.append("logical design is infeasible")
        if missing: return FeasibilityResult("blocked_pending_site_data", logical_feasible, False, reasons, missing, False)
        if proposed_rack_units > (site.available_rack_units or 0): reasons.append("rack capacity exceeded")
        if proposed_feeds > (site.available_power_feeds or 0): reasons.append("power feeds exceeded")
        if require_redundancy and (site.available_power_feeds or 0) < 2: reasons.append("power redundancy cannot be demonstrated")
        if site.installer_limitations: reasons.append("installer limitations require review")
        if reasons: return FeasibilityResult("blocked_due_to_constraints", logical_feasible, False, reasons, [], False)
        if site.assumptions: return FeasibilityResult("feasible_with_assumptions", logical_feasible, True, ["explicit assumptions remain"], [], True)
        return FeasibilityResult("feasible", logical_feasible, True, [], [], True)
