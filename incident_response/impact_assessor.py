"""Impact and blast-radius assessment for incidents."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord

from ._common import make_assumption, make_decision
from .incident_models import BusinessImpact, ImpactAssessment


class ImpactAssessor:
    """Assess explicit scope and dependency maps without fabricating impact."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def assess(self, *, affected_devices: Sequence[str] = (), affected_services: Sequence[str] = (), affected_sites: Sequence[str] = (), affected_users: int | None = None, dependency_map: Mapping[str, Sequence[str]] | None = None, topology_links: Mapping[str, Sequence[str]] | None = None, business_impact: Mapping[str, Any] | None = None, compliance_context: Mapping[str, Any] | None = None) -> ImpactAssessment:
        """Calculate bounded blast radius from supplied topology and dependency data."""
        devices = list(dict.fromkeys(str(item) for item in affected_devices))
        services = list(dict.fromkeys(str(item) for item in affected_services))
        sites = list(dict.fromkeys(str(item) for item in affected_sites))
        dependencies_considered: list[str] = []
        if dependency_map is None:
            self.assumptions.append(make_assumption("impact:dependency_map", "not_supplied", "service blast radius is not inferred from names alone", True))
        else:
            for service in services:
                dependencies_considered.extend(str(item) for item in dependency_map.get(service, []))
        if topology_links is None:
            self.assumptions.append(make_assumption("impact:topology_links", "not_supplied", "topological spread is not inferred without explicit links", True))
        else:
            for device in devices:
                dependencies_considered.extend(str(item) for item in topology_links.get(device, []))
        if affected_users is None:
            self.assumptions.append(make_assumption("impact:affected_users", "unknown", "user impact remains unknown without an explicit estimate", True))
        if not devices and not services and not sites:
            blast_radius = "unknown"
            confidence = 0.0
        elif len(sites) > 1 or len(devices) > 10 or len(services) > 5:
            blast_radius = "multi_site_or_broad"
            confidence = 0.7 if dependency_map is not None or topology_links is not None else 0.4
        elif len(devices) > 1 or len(services) > 1:
            blast_radius = "multi_component"
            confidence = 0.65 if dependency_map is not None or topology_links is not None else 0.35
        else:
            blast_radius = "localized"
            confidence = 0.75
        supplied_business = dict(business_impact or {})
        supplied_compliance = dict(compliance_context or {})
        if not supplied_business:
            self.assumptions.append(make_assumption("impact:business", "unknown", "revenue, operational, and reputation impact are not inferred without business data", True))
        if not supplied_compliance:
            self.assumptions.append(make_assumption("impact:compliance", "unknown", "regulatory notification is not inferred without authoritative context", True))
        business = BusinessImpact(revenue_impact=str(supplied_business.get("revenue_impact", "unknown")), operational_impact=str(supplied_business.get("operational_impact", "unknown")), reputation_impact=str(supplied_business.get("reputation_impact", "unknown")), compliance_impact=str(supplied_compliance.get("compliance_impact", supplied_business.get("compliance_impact", "unknown"))), regulatory_notification_required=supplied_compliance.get("regulatory_notification_required"), confidence=0.8 if supplied_business or supplied_compliance else 0.0, assumptions=[item.key for item in self.assumptions])
        decision = make_decision("ImpactAssessor", "impact-assessment", blast_radius, "use explicit device, service, site, dependency, and topology inputs only", ["localized", "multi_component", "multi_site_or_broad", "unknown"], {item: "not selected by supplied scope" for item in ["localized", "multi_component", "multi_site_or_broad", "unknown"] if item != blast_radius})
        self.decisions.append(decision)
        return ImpactAssessment(affected_devices=devices, affected_services=services, affected_users_estimate=affected_users, affected_sites=sites, business_impact=business, blast_radius=blast_radius, dependencies_considered=list(dict.fromkeys(dependencies_considered)), confidence=confidence, assumptions=[item.key for item in self.assumptions])
