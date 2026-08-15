"""Shared helpers for V1 service configuration artifacts."""
from __future__ import annotations

from typing import Any, Iterable

from .service_orchestrator import ServiceBase, ServiceConfigArtifact, ServiceState


def missing(request: dict[str, Any], fields: Iterable[str]) -> tuple[str, ...]:
    """Return fields absent from an explicit request."""
    return tuple(field for field in fields if field not in request or request[field] in (None, "", []))


def secret_references(request: dict[str, Any], keys: Iterable[str]) -> tuple[str, ...]:
    """Extract only secret:// references and reject inline secret material."""
    references: list[str] = []
    for key in keys:
        value = request.get(key)
        if value is None:
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            if not isinstance(item, str) or not item.startswith("secret://"):
                raise ValueError(f"{key} must contain secret:// references only")
            references.append(item)
    return tuple(dict.fromkeys(references))


def external_preview(service: ServiceBase, request: dict[str, Any], integration_name: str) -> ServiceConfigArtifact | None:
    """Return a preview-only artifact when an external integration lacks explicit confirmation."""
    if request.get("external_integration") and not bool(request.get("external_integration_confirmed", False)):
        return service._artifact(ServiceState.PREVIEW_ONLY.value, {"external_integration": integration_name, "configuration": "not emitted until human confirmation"}, required_human_inputs=(f"{integration_name}.external_integration_confirmed",), external_integrations=(integration_name,), assumption_ids=(f"assumption:{service.definition.name}:external-integration",))
    return None


def as_list(value: Any) -> list[Any]:
    """Normalize an explicitly supplied list without inventing elements."""
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("service list fields must be lists")
    return list(value)
