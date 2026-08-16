"""Authorization boundaries for local network discovery."""

from __future__ import annotations

import ipaddress

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import DiscoveryTarget, ManagementProtocol


class AuthorizedScope(BaseModel):
    """Human-approved local management ranges, targets, and read-only protocols."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    site_id: str = Field(min_length=1, max_length=160)
    approved_networks: tuple[str, ...] = Field(min_length=1)
    approved_targets: tuple[str, ...] = Field(min_length=1)
    allowed_protocols: tuple[ManagementProtocol, ...] = Field(min_length=1)
    approval_reference: str = Field(min_length=1, max_length=200)
    operator_acknowledged: bool = False

    @field_validator("approved_networks")
    @classmethod
    def validate_networks(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Ensure every registered management range is a valid IP network."""

        for value in values:
            ipaddress.ip_network(value, strict=False)
        return values

    @field_validator("approved_targets")
    @classmethod
    def validate_targets(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Ensure every explicitly approved target is a valid IP address."""

        normalized: list[str] = []
        for value in values:
            normalized.append(str(ipaddress.ip_address(value)))
        return tuple(normalized)

    def authorizes(self, target: DiscoveryTarget) -> bool:
        """Return whether the scope authorizes a target without attempting a connection."""

        if not self.operator_acknowledged or target.protocol not in self.allowed_protocols:
            return False
        try:
            address = ipaddress.ip_address(target.address)
        except ValueError:
            return False
        normalized_address = str(address)
        if normalized_address not in self.approved_targets:
            return False
        return any(address in ipaddress.ip_network(network, strict=False) for network in self.approved_networks)
