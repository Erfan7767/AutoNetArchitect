"""Direct and indirect impact analysis for network changes."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord

from .change_models import ChangeRequest, ImpactAssessment, ImpactClass


class ChangeImpactAnalyzer:
    """Analyze blast radius from explicit dependency and scope data."""

    def analyze(
        self,
        request: ChangeRequest,
        *,
        dependency_map: Mapping[str, Sequence[str]] | None = None,
        service_dependency_map: Mapping[str, Sequence[str]] | None = None,
        user_counts: Mapping[str, int] | None = None,
        expected_downtime: timedelta = timedelta(0),
        performance_degradation_window: timedelta = timedelta(0),
        complete_service_outage: bool = False,
    ) -> ImpactAssessment:
        """Return impact assessment without inventing user counts or dependencies."""
        direct_devices = tuple(dict.fromkeys(device.device_id for device in request.affected_devices))
        dependency_map = dependency_map or {}
        indirect: set[str] = set()
        for device_id in direct_devices:
            indirect.update(str(item) for item in dependency_map.get(device_id, ()))
        indirect.difference_update(direct_devices)
        services = {service.service_id for service in request.affected_services}
        for service_id in tuple(services):
            services.update(str(item) for item in (service_dependency_map or {}).get(service_id, ()))
        sites = {site.site_id for site in request.affected_sites}
        sites.update(device.site_id for device in request.affected_devices if device.site_id)
        estimated_users: int | None = None
        if user_counts is not None:
            estimated_users = sum(int(user_counts.get(identifier, 0)) for identifier in set(direct_devices) | sites | services)
        impact = self._impact_class(expected_downtime, complete_service_outage)
        rationale = f"impact derived from {len(direct_devices)} direct devices, {len(indirect)} indirect devices, {len(services)} services, and {len(sites)} sites"
        assessment = ImpactAssessment(direct_devices, tuple(sorted(indirect)), tuple(sorted(services)), estimated_users, tuple(sorted(sites)), expected_downtime, performance_degradation_window, impact, rationale, tuple(request.history_ids))
        request.impact_assessment = assessment
        request.status = "impact_assessed"
        request.decision_records.append(DecisionRecord("ChangeImpactAnalyzer", f"{request.change_id}:impact", impact, ["scope_only", "dependency_expanded"], {"scope_only": "indirect dependencies were supplied", "dependency_expanded": "selected when dependency evidence exists"}))
        if user_counts is None:
            request.assumptions.append(Assumption("affected_user_count", "unknown", "user impact count is not inferred from device count", True))
        if dependency_map is None:
            request.assumptions.append(Assumption("device_dependencies", "unknown", "indirect device impact requires an explicit dependency map", True))
        return assessment

    @staticmethod
    def _impact_class(downtime: timedelta, outage: bool) -> str:
        """Classify expected impact from explicit duration."""
        if outage:
            return ImpactClass.SERVICE_OUTAGE.value
        seconds = max(0.0, downtime.total_seconds())
        if seconds == 0:
            return ImpactClass.NO_IMPACT.value
        if seconds < 60:
            return ImpactClass.MINOR_IMPACT.value
        if seconds <= 1800:
            return ImpactClass.MODERATE_IMPACT.value
        return ImpactClass.MAJOR_IMPACT.value
