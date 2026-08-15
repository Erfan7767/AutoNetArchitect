"""Human-led P1 war-room coordination."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from ._common import make_assumption, make_decision
from .incident_models import Incident, IncidentSeverity


class WarRoomActionItem(BaseModel):
    """War-room action item with owner and deadline."""

    model_config = ConfigDict(extra="forbid")

    action_id: str
    description: str
    owner: str
    deadline: datetime | None = None
    status: str = "open"


class WarRoomArtifact(BaseModel):
    """War-room state and coordination artifact."""

    model_config = ConfigDict(extra="forbid")

    war_room_id: str
    incident_id: str
    incident_commander: str
    participant_list: list[str] = Field(default_factory=list)
    action_items: list[WarRoomActionItem] = Field(default_factory=list)
    decision_log: list[dict[str, Any]] = Field(default_factory=list)
    status_timeline: list[dict[str, Any]] = Field(default_factory=list)
    current_diagnosis_summary: str = ""
    next_actions: list[str] = Field(default_factory=list)
    next_update_due_at: datetime
    active: bool = True


class WarRoomCoordinator:
    """Create and update war-room artifacts only for human-led P1 coordination."""

    def __init__(self) -> None:
        """Initialize local war-room repository."""
        self._rooms: dict[str, WarRoomArtifact] = {}
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def initiate(self, incident: Incident, *, incident_commander: str, participants: Sequence[str], current_diagnosis_summary: str = "") -> WarRoomArtifact:
        """Initiate a war room only when a human commander is supplied for P1."""
        if incident.severity != IncidentSeverity.P1_CRITICAL:
            raise ValueError("war rooms are mandatory only for P1 incidents in V1")
        if not incident_commander or incident_commander.lower() in {"system", "unknown", "automatic"}:
            raise ValueError("a human incident commander is required")
        if not participants:
            self.assumptions.append(make_assumption(f"{incident.incident_id}:war_room_participants", "minimal", "participant contacts must be supplied by the commander", True))
        room_id = f"WAR-{incident.incident_id}"
        now = datetime.now(timezone.utc)
        artifact = WarRoomArtifact(war_room_id=room_id, incident_id=incident.incident_id, incident_commander=incident_commander, participant_list=list(dict.fromkeys([incident_commander, *participants])), current_diagnosis_summary=current_diagnosis_summary, next_update_due_at=now + timedelta(minutes=30), status_timeline=[{"timestamp": now.isoformat(), "event": "initiated", "performed_by": incident_commander}], next_actions=["confirm scope", "maintain evidence", "publish next status update"])
        self._rooms[room_id] = artifact
        decision = make_decision("WarRoomCoordinator", f"{incident.incident_id}:war-room:initiate", "human_led_p1_war_room", "P1 incident and human commander satisfy war-room policy", ["human_led_p1_war_room", "automatic_war_room"], {"human_led_p1_war_room": "selected", "automatic_war_room": "rejected"})
        self.decisions.append(decision)
        return artifact.model_copy(deep=True)

    def get(self, war_room_id: str) -> WarRoomArtifact:
        """Return a war-room artifact copy."""
        if war_room_id not in self._rooms:
            raise KeyError(f"unknown war room: {war_room_id}")
        return self._rooms[war_room_id].model_copy(deep=True)

    def add_action(self, war_room_id: str, *, description: str, owner: str, deadline: datetime | None = None) -> WarRoomArtifact:
        """Add a human-owned action item."""
        room = self._rooms.get(war_room_id)
        if room is None:
            raise KeyError(f"unknown war room: {war_room_id}")
        if not description or not owner:
            raise ValueError("description and owner are required")
        item = WarRoomActionItem(action_id=f"{war_room_id}:action:{len(room.action_items)+1}", description=description, owner=owner, deadline=deadline)
        room.action_items.append(item)
        room.next_actions.append(description)
        return room.model_copy(deep=True)

    def update(self, war_room_id: str, *, actor: str, diagnosis_summary: str | None = None, decision: str | None = None, next_actions: Sequence[str] = ()) -> WarRoomArtifact:
        """Append a status update and optional decision to the artifact."""
        room = self._rooms.get(war_room_id)
        if room is None:
            raise KeyError(f"unknown war room: {war_room_id}")
        now = datetime.now(timezone.utc)
        room.status_timeline.append({"timestamp": now.isoformat(), "event": "update", "performed_by": actor})
        room.next_update_due_at = now + timedelta(minutes=30)
        if diagnosis_summary is not None:
            room.current_diagnosis_summary = diagnosis_summary
        if decision:
            room.decision_log.append({"timestamp": now.isoformat(), "performed_by": actor, "decision": decision})
        if next_actions:
            room.next_actions = list(next_actions)
        return room.model_copy(deep=True)

    def close(self, war_room_id: str, *, actor: str, reason: str) -> WarRoomArtifact:
        """Close a war room after a human status decision."""
        room = self._rooms.get(war_room_id)
        if room is None:
            raise KeyError(f"unknown war room: {war_room_id}")
        if not actor or not reason:
            raise ValueError("actor and reason are required")
        room.active = False
        room.status_timeline.append({"timestamp": datetime.now(timezone.utc).isoformat(), "event": "closed", "performed_by": actor, "reason": reason})
        return room.model_copy(deep=True)
