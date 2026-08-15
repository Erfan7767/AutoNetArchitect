from __future__ import annotations

from typing import Any

from .common import EnterpriseDomainBase


class EnterpriseCampusPatterns(EnterpriseDomainBase):
    """Campus access/distribution/core patterns with scale-aware alternatives."""

    def design(self, requirements: dict[str, Any]) -> dict[str, Any]:
        guard = self.guard_domain(requirements)
        if not guard["applicable"]:
            return self.envelope(requirements, {"status": guard["status"]})
        patterns = {
            "small": {"layers": ["access", "collapsed_core"], "routing_boundary": "collapsed_core"},
            "medium": {"layers": ["access", "distribution", "core"], "routing_boundary": "distribution"},
            "large": {"layers": ["access", "distribution", "core"], "routing_boundary": "distribution_or_core", "core": "redundant"},
        }
        scale = requirements.get("campus_scale", "medium")
        selected = patterns.get(scale, patterns["medium"])
        if scale not in patterns:
            self.record_assumption("campus_scale", scale, "Campus scale requires validation from site and endpoint inventory.")
        self.record_decision("enterprise_campus_pattern", selected["layers"], "Campus layers are selected by explicit campus scale.")
        return self.envelope(requirements, {"selected_scale": scale, "pattern": selected, "patterns": patterns})
