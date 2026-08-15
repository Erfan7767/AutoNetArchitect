"""Dependency-aware service orchestration contracts for V1 infrastructure support."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable


class ServiceState(str, Enum):
    """Lifecycle state for a service configuration artifact."""

    GENERATED = "generated"
    PREVIEW_ONLY = "preview_only"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    BLOCKED_DEPENDENCY = "blocked_dependency"


class HealthState(str, Enum):
    """Health states that avoid claiming operational success without observations."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ServiceDefinition:
    """Static service dependency and scope definition."""

    name: str
    dependencies: tuple[str, ...] = ()
    scope: str = "local_infrastructure_support"
    external_integration_assumed: bool = False
    description: str = ""
    health_checks: tuple[str, ...] = ()


@dataclass(frozen=True)
class ServiceHealth:
    """Auditable health result for one service."""

    service: str
    state: str
    healthy: bool | None
    detail: str
    checks: dict[str, Any] = field(default_factory=dict)
    required_human_inputs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize health without hidden runtime claims."""
        return asdict(self) | {"required_human_inputs": list(self.required_human_inputs)}


@dataclass(frozen=True)
class ServiceConfigArtifact:
    """Versioned, traceable configuration artifact for one service."""

    service: str
    artifact_id: str
    schema_version: str
    state: str
    config: dict[str, Any]
    dependencies: tuple[str, ...] = ()
    decision_ids: tuple[str, ...] = ()
    assumption_ids: tuple[str, ...] = ()
    required_human_inputs: tuple[str, ...] = ()
    external_integrations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the artifact."""
        return asdict(self) | {
            "dependencies": list(self.dependencies),
            "decision_ids": list(self.decision_ids),
            "assumption_ids": list(self.assumption_ids),
            "required_human_inputs": list(self.required_human_inputs),
            "external_integrations": list(self.external_integrations),
        }


class ServiceBase:
    """Base implementation shared by all service configuration designers."""

    SCHEMA_VERSION = "1.0"
    definition = ServiceDefinition("undefined")

    def generate(self, request: dict[str, Any]) -> ServiceConfigArtifact:
        """Generate an artifact from explicit inputs; concrete service classes provide the implementation."""
        raise TypeError(f"a concrete service generator is required for {self.definition.name}")

    def health(self, observation: dict[str, Any] | None = None) -> ServiceHealth:
        """Return unknown until a caller supplies an explicit health observation."""
        observation = observation or {}
        if not observation:
            return ServiceHealth(
                self.definition.name,
                HealthState.UNKNOWN.value,
                None,
                "no runtime health observation supplied",
                {check: HealthState.UNKNOWN.value for check in self.definition.health_checks},
            )
        healthy = observation.get("healthy")
        if healthy is True:
            return ServiceHealth(
                self.definition.name,
                HealthState.HEALTHY.value,
                True,
                str(observation.get("detail", "explicit observation reports healthy")),
                dict(observation.get("checks", {})),
            )
        if healthy is False:
            return ServiceHealth(
                self.definition.name,
                HealthState.DEGRADED.value,
                False,
                str(observation.get("detail", "explicit observation reports unhealthy")),
                dict(observation.get("checks", {})),
            )
        return ServiceHealth(
            self.definition.name,
            HealthState.UNKNOWN.value,
            None,
            "health observation does not contain a boolean healthy value",
            dict(observation.get("checks", {})),
        )

    def blocked(self, reason: str, required_human_inputs: Iterable[str] = (), dependencies: Iterable[str] = ()) -> ServiceConfigArtifact:
        """Create an explicit blocked artifact."""
        return self._artifact(
            ServiceState.BLOCKED_DEPENDENCY.value if dependencies else ServiceState.BLOCKED_MISSING_HUMAN_DATA.value,
            {},
            required_human_inputs=required_human_inputs,
            dependencies=dependencies,
            assumption_ids=(f"assumption:{self.definition.name}:blocked",),
        )

    def _artifact(
        self,
        state: str,
        config: dict[str, Any],
        dependencies: Iterable[str] | None = None,
        decision_ids: Iterable[str] = (),
        assumption_ids: Iterable[str] = (),
        required_human_inputs: Iterable[str] = (),
        external_integrations: Iterable[str] = (),
    ) -> ServiceConfigArtifact:
        dependency_tuple = tuple(dependencies if dependencies is not None else self.definition.dependencies)
        decision_tuple = tuple(dict.fromkeys(str(value) for value in decision_ids))
        assumption_tuple = tuple(dict.fromkeys(str(value) for value in assumption_ids))
        human_tuple = tuple(dict.fromkeys(str(value) for value in required_human_inputs))
        external_tuple = tuple(dict.fromkeys(str(value) for value in external_integrations))
        unsigned = {
            "service": self.definition.name,
            "schema_version": self.SCHEMA_VERSION,
            "state": state,
            "config": config,
            "dependencies": dependency_tuple,
            "decision_ids": decision_tuple,
            "assumption_ids": assumption_tuple,
            "required_human_inputs": human_tuple,
            "external_integrations": external_tuple,
        }
        digest = hashlib.sha256(json.dumps(unsigned, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return ServiceConfigArtifact(
            self.definition.name,
            f"service-config:{self.definition.name}:{digest[:16]}",
            self.SCHEMA_VERSION,
            state,
            config,
            dependency_tuple,
            decision_tuple,
            assumption_tuple,
            human_tuple,
            external_tuple,
        )


class ServiceOrchestrator:
    """Order services by dependencies and aggregate artifacts and health results."""

    def __init__(self, services: Iterable[ServiceBase] | None = None) -> None:
        self._services = {service.definition.name: service for service in (services or self.default_services())}
        self._validate_definitions()

    @staticmethod
    def default_services() -> tuple[ServiceBase, ...]:
        """Import and return the supported V1 service implementations."""
        from .aaa_service import AAAService
        from .dhcp_service import DHCPService
        from .dns_service import DNSService
        from .nms_service import NMSService
        from .ntp_service import NTPService
        from .os_hardening import OSHardeningService
        from .pki_service import PKIService
        from .siem_service import SIEMService
        from .snmp_service import SNMPService
        from .syslog_service import SyslogService

        return (
            NTPService(),
            DNSService(),
            SyslogService(),
            AAAService(),
            SNMPService(),
            DHCPService(),
            PKIService(),
            SIEMService(),
            NMSService(),
            OSHardeningService(),
        )

    def register(self, service: ServiceBase) -> None:
        """Register or replace a service implementation."""
        self._services[service.definition.name] = service
        self._validate_definitions()

    def service(self, name: str) -> ServiceBase:
        """Return one registered service."""
        try:
            return self._services[name]
        except KeyError as exc:
            raise KeyError(f"unknown service: {name}") from exc

    def deployment_order(self) -> tuple[str, ...]:
        """Return a deterministic topological order or raise on missing/cyclic dependencies."""
        pending = {name: set(service.definition.dependencies) for name, service in self._services.items()}
        order: list[str] = []
        while pending:
            ready = sorted(name for name, dependencies in pending.items() if not dependencies)
            if not ready:
                raise ValueError("service dependency cycle detected")
            order.extend(ready)
            for name in ready:
                pending.pop(name)
            for dependencies in pending.values():
                dependencies.difference_update(ready)
        return tuple(order)

    def generate_all(self, requests: dict[str, dict[str, Any]] | None = None) -> tuple[ServiceConfigArtifact, ...]:
        """Generate artifacts in dependency order and block downstream services when dependencies block."""
        requests = requests or {}
        artifacts: dict[str, ServiceConfigArtifact] = {}
        for name in self.deployment_order():
            service = self._services[name]
            failed_dependencies = tuple(
                dependency
                for dependency in service.definition.dependencies
                if artifacts[dependency].state not in {ServiceState.GENERATED.value, ServiceState.PREVIEW_ONLY.value}
            )
            if failed_dependencies:
                artifacts[name] = service.blocked("dependency artifact is blocked", dependencies=failed_dependencies)
            else:
                artifacts[name] = service.generate(dict(requests.get(name, {})))
        return tuple(artifacts[name] for name in self.deployment_order())

    def health_all(self, observations: dict[str, dict[str, Any]] | None = None) -> tuple[ServiceHealth, ...]:
        """Return health definitions for all services in deployment order."""
        observations = observations or {}
        return tuple(self._services[name].health(observations.get(name)) for name in self.deployment_order())

    def _validate_definitions(self) -> None:
        names = set(self._services)
        for name, service in self._services.items():
            if name != service.definition.name:
                raise ValueError(f"service registry key mismatch: {name}")
            missing = set(service.definition.dependencies) - names
            if missing:
                raise ValueError(f"service {name} has unknown dependencies: {sorted(missing)}")
