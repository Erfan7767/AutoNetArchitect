"""Explicit callback adapters for Incident Response cross-layer integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


IncidentCallback = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True)
class IncidentIntegrationAdapters:
    """Human-controlled callback boundary for optional project layers."""

    monitoring: IncidentCallback | None = None
    change_management: IncidentCallback | None = None
    governance: IncidentCallback | None = None
    learning_memory: IncidentCallback | None = None
    operations: IncidentCallback | None = None
    dr_bc: IncidentCallback | None = None
    security: IncidentCallback | None = None

    def configured(self) -> dict[str, bool]:
        """Return configuration status without exposing callback internals."""
        return {"monitoring": self.monitoring is not None, "change_management": self.change_management is not None, "governance": self.governance is not None, "learning_memory": self.learning_memory is not None, "operations": self.operations is not None, "dr_bc": self.dr_bc is not None, "security": self.security is not None}
