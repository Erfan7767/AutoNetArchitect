"""Authorization-bound target scope enforcement for local discovery."""

from __future__ import annotations

import ipaddress

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import DiscoveryTarget, ManagementProtocol


class AuthorizedScope(BaseModel):
    """Human-approved local management ranges and permitted read-only protocols."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    site_id: str = Field(min_length=1, max_length=160)
    approved_networks: tuple[str, ...] = Field(min_length=1)
    allowed_protocols: tuple[ManagementProtocol, ...] = Field(min_length=1)
    approval_reference: str = Field(min_length=1, max_length=200)

    @field_validator("approved_networks")
    @classmethod
    def validate_networks(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Ensure every registered management range is a valid IP network."""

        for value in values:
            ipaddress.ip_network(value, strict=False)
        return values

    def authorizes(self, target: DiscoveryTarget) -> bool:
        """Return whether the scope authorizes a target without attempting a connection."""

        if target.protocol not in self.allowed_protocols:
            return False
        try:
            address = ipaddress.ip_address(target.address)
        except ValueError:
            return False
        return any(address in ipaddress.ip_network(network, strict=False) for network in self.approved_networks)
