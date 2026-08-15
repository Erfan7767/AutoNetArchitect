"""Pure device-card view model for the V1 UI shell."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ui.state_manager import mask_for_ui


@dataclass(frozen=True)
class DeviceCard:
    """Secret-safe display model for one device."""

    device_id: str
    label: str
    vendor: str
    platform: str
    status: str
    metadata: dict[str, Any]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DeviceCard":
        """Build a card from an external device mapping."""
        if not isinstance(payload, Mapping):
            raise ValueError("device payload must be a mapping")
        device_id = str(payload.get("device_id", ""))
        if not device_id:
            raise ValueError("device_id is required")
        return cls(
            device_id=device_id,
            label=str(payload.get("label", device_id)),
            vendor=str(payload.get("vendor", "unknown")),
            platform=str(payload.get("platform", "unknown")),
            status=str(payload.get("status", "unknown")),
            metadata=dict(mask_for_ui(dict(payload.get("metadata", {})))),
        )

    def render(self) -> dict[str, Any]:
        """Return a UI-safe card mapping."""
        return {"device_id": self.device_id, "label": self.label, "vendor": self.vendor, "platform": self.platform, "status": self.status, "metadata": mask_for_ui(self.metadata)}
