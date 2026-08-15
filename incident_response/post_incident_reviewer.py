"""Blame-free post-incident review generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord

from ._common import make_assumption, make_decision
from .incident_models import Incident, IncidentReview, IncidentSeverity, ReviewActionItem


class PostIncidentReviewer:
    """Create review artifacts and learning/change follow-up without external writes."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def create_review(self, incident: Incident, *, what_went_well: Sequence[str] = (), improvements: Sequence[str] = (), detection_effectiveness: str = "unknown", response_effectiveness: str = "unknown", communication_effectiveness: str = "unknown", tool_effectiveness: str = "unknown", process_gaps: Sequence[str] = (), action_items: Sequence[Mapping[str, Any]] = (), knowledge_updates: Sequence[str] = ()) -> IncidentReview:
        """Create a required review for P1/P2 and a recommended review for P3."""
        required = incident.severity in {IncidentSeverity.P1_CRITICAL, IncidentSeverity.P2_HIGH}
        if not required and incident.severity == IncidentSeverity.P3_MEDIUM:
            self.assumptions.append(make_assumption(f"{incident.incident_id}:review", "recommended", "P3 review is recommended but not mandatory unless recurrence is supplied", True))
        if not incident.root_cause:
            self.assumptions.append(make_assumption(f"{incident.incident_id}:review_root_cause", "unknown", "review does not invent a root cause when the incident record lacks one", True))
        items: list[ReviewActionItem] = []
        for index, item in enumerate(action_items, start=1):
            description = str(item.get("description", ""))
            owner = str(item.get("owner", ""))
            if not description or not owner:
                self.assumptions.append(make_assumption(f"{incident.incident_id}:review_action:{index}", "incomplete", "action item requires explicit description and owner", True))
                continue
            due_date = item.get("due_date")
            parsed_due = datetime.fromisoformat(str(due_date).replace("Z", "+00:00")) if due_date else None
            items.append(ReviewActionItem(action_id=f"{incident.incident_id}:review-action:{index}", action_type=str(item.get("action_type", "corrective")), description=description, owner=owner, due_date=parsed_due, related_change_reference=str(item.get("related_change_reference", "")) or None))
        if not items:
            self.assumptions.append(make_assumption(f"{incident.incident_id}:review_actions", "not_supplied", "follow-up actions are not fabricated", True))
        decision = make_decision("PostIncidentReviewer", f"{incident.incident_id}:post-review", "blame_free_process_review", "focus review on systems, controls, detection, response, and process gaps", ["blame_free_process_review", "individual_blame"], {"blame_free_process_review": "selected", "individual_blame": "rejected"})
        self.decisions.append(decision)
        return IncidentReview(review_id=f"PIR-{incident.incident_id}", incident_id=incident.incident_id, required=required, incident_summary=f"{incident.title}: {incident.description}", timeline_review=f"{len(incident.timeline)} timeline entries recorded", root_cause_analysis=incident.root_cause or "not established from current evidence", what_went_well=list(what_went_well), improvements=list(improvements), detection_effectiveness=detection_effectiveness, response_effectiveness=response_effectiveness, communication_effectiveness=communication_effectiveness, tool_effectiveness=tool_effectiveness, process_gaps=list(process_gaps), action_items=items, knowledge_updates=list(knowledge_updates), blame_free=True)
