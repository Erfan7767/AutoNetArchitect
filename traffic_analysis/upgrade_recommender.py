"""Governed capacity upgrade recommendations."""
from __future__ import annotations
from typing import Any, Callable, Mapping
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import UpgradeRecommendation

class UpgradeRecommender:
    """Suggest capacity steps without fabricating equipment models or costs."""
    CAPACITY_STEPS = (1.0, 10.0, 25.0, 40.0, 100.0, 400.0)
    def __init__(self, equipment_lookup: Callable[[float], Mapping[str, Any] | None] | None = None) -> None:
        """Initialize optional equipment evidence lookup."""
        self.equipment_lookup = equipment_lookup
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def recommend(self, *, subject_id: str, current_capacity_mbps: float | None, required_capacity_mbps: float | None, bottleneck: str = "", target_date: str = "review_required") -> UpgradeRecommendation:
        """Return a recommendation only when current and required capacities are explicit."""
        if current_capacity_mbps is None or required_capacity_mbps is None:
            self.assumptions.append(make_assumption(f"upgrade:{subject_id}:capacity", "unknown", "capacity upgrade cannot select a target without current and required capacity", True))
            return UpgradeRecommendation(recommendation_id=f"upgrade:{subject_id}", subject_id=subject_id, current_capacity_mbps=current_capacity_mbps, required_capacity_mbps=required_capacity_mbps, recommended_solution="blocked_pending_capacity_data", implementation_complexity="unknown", required_downtime="unknown", recommended_timeline=target_date, assumptions=[item.key for item in self.assumptions])
        if required_capacity_mbps <= current_capacity_mbps:
            solution = "no_capacity_upgrade_required"
            target = current_capacity_mbps
        else:
            target = next((step for step in self.CAPACITY_STEPS if step >= required_capacity_mbps), None)
            solution = f"upgrade_link_to_{target:g}_Mbps" if target is not None else "capacity_target_exceeds_v1_catalog"
            if target is None:
                self.assumptions.append(make_assumption(f"upgrade:{subject_id}:target", "unsupported", "required target exceeds V1 capacity step catalog", True))
        if self.equipment_lookup is not None and target is not None:
            evidence = self.equipment_lookup(target)
            if evidence is None:
                self.assumptions.append(make_assumption(f"upgrade:{subject_id}:equipment", "not_found", "no capability/equipment evidence was returned for the target", True))
        else:
            self.assumptions.append(make_assumption(f"upgrade:{subject_id}:equipment", "not_connected", "equipment selector/BOM integration was not supplied", True))
        decision = make_decision("UpgradeRecommender", f"upgrade:{subject_id}", solution, "select a capacity step only from the supported numeric catalog and keep equipment selection evidence-gated", ["capacity_step_upgrade", "invent_model", "no_upgrade"], {"capacity_step_upgrade": "selected when required exceeds current", "invent_model": "rejected", "no_upgrade": "selected only when current is sufficient"})
        self.decisions.append(decision)
        return UpgradeRecommendation(recommendation_id=f"upgrade:{subject_id}", subject_id=subject_id, current_capacity_mbps=current_capacity_mbps, required_capacity_mbps=required_capacity_mbps, recommended_solution=solution, target_capacity_mbps=target, estimated_cost="unknown", implementation_complexity="medium" if target and target > current_capacity_mbps else "low", required_downtime="requires change planning" if target and target > current_capacity_mbps else "none", recommended_timeline=target_date, assumptions=[item.key for item in self.assumptions])
