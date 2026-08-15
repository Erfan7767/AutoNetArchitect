"""Capacity planning from current links and growth forecasts."""
from __future__ import annotations
from typing import Mapping, Sequence
from pydantic import BaseModel, ConfigDict, Field
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import GrowthProjection, TrafficLinkModel, UpgradeRecommendation
from .upgrade_recommender import UpgradeRecommender

class CapacityPlan(BaseModel):
    """Capacity planning artifact."""
    model_config = ConfigDict(extra="forbid")
    current_state: list[dict[str, object]] = Field(default_factory=list)
    forecast: list[GrowthProjection] = Field(default_factory=list)
    recommendations: list[UpgradeRecommendation] = Field(default_factory=list)
    budget_estimate: str = "unknown"
    timeline: str = "review_required"
    assumptions: list[str] = Field(default_factory=list)

class CapacityPlanner:
    """Plan capacity upgrades while keeping costs and models evidence-gated."""
    def __init__(self, recommender: UpgradeRecommender | None = None) -> None:
        """Initialize planner."""
        self.recommender = recommender or UpgradeRecommender()
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def plan(self, *, links: Sequence[TrafficLinkModel], required_by_link: Mapping[str, float], forecasts: Sequence[GrowthProjection] = (), budget_estimate: str = "unknown", timeline: str = "review_required") -> CapacityPlan:
        """Create current-state, forecast, and upgrade recommendation sections."""
        current = [{"link_id": link.link_id, "capacity_mbps": link.link_speed_mbps, "source": link.traffic_data.source.value, "peak_utilization_percent": link.traffic_data.peak_utilization_percent} for link in links]
        recommendations = [self.recommender.recommend(subject_id=link.link_id, current_capacity_mbps=link.link_speed_mbps, required_capacity_mbps=required_by_link.get(link.link_id), target_date=timeline) for link in links if link.link_id in required_by_link]
        if budget_estimate == "unknown":
            self.assumptions.append(make_assumption("capacity-plan:budget", "unknown", "budget is not inferred from technical capacity alone", True))
        if not links:
            self.assumptions.append(make_assumption("capacity-plan:links", "none", "no explicit links supplied", True))
        self.decisions.append(make_decision("CapacityPlanner", "capacity-plan", "current_forecast_recommendation", "separate current evidence, forecast assumptions, and governed recommendations", ["current_forecast_recommendation", "fabricate_budget_or_model"], {"current_forecast_recommendation": "selected", "fabricate_budget_or_model": "rejected"}))
        return CapacityPlan(current_state=current, forecast=list(forecasts), recommendations=recommendations, budget_estimate=budget_estimate, timeline=timeline, assumptions=[item.key for item in self.assumptions])
