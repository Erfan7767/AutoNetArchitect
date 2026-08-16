"""Read-only reachability probe for explicitly authorized discovery targets."""

from __future__ import annotations

import socket
from dataclasses import dataclass

from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol


PORT_BY_PROTOCOL: dict[ManagementProtocol, int] = {
    ManagementProtocol.SSH: 22,
    ManagementProtocol.NETCONF: 830,
    ManagementProtocol.HTTPS_API: 443,
    ManagementProtocol.SNMP: 161,
}


@dataclass(frozen=True)
class ReadOnlyReachabilityProbe:
    """Performs a bounded TCP connectivity check without authentication, mutation, or credential use."""

    timeout_seconds: float = 2.0

    def collect(self, target: DiscoveryTarget) -> DiscoveryResult:
        """Return reachability evidence and never infer vendor, model, version, or configuration facts."""

        port = PORT_BY_PROTOCOL[target.protocol]
        if target.protocol is ManagementProtocol.SNMP:
            return DiscoveryResult(
                target=target,
                state=DiscoveryState.UNSUPPORTED,
                message="SNMP discovery requires an approved collector adapter and is not attempted by the TCP reachability probe.",
            )
        try:
            with socket.create_connection((target.address, port), timeout=self.timeout_seconds):
                return DiscoveryResult(
                    target=target,
                    state=DiscoveryState.AMBIGUOUS,
                    message=(
                        f"The approved {target.protocol.value} endpoint responded on port {port}. "
                        "Vendor, platform, version, and capabilities remain unobserved until a supported read-only adapter supplies evidence."
                    ),
                )
        except OSError as error:
            return DiscoveryResult(
                target=target,
                state=DiscoveryState.UNREACHABLE,
                message=f"The approved {target.protocol.value} endpoint was not reachable: {error.__class__.__name__}.",
            )
