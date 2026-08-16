"""Read-only local-neighbor inventory collection for Windows-managed discovery workflows."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass

from site_agent.models import DiscoveryTarget, ManagementProtocol
from site_agent.scope import AuthorizedScope


WINDOWS_ARP_PATTERN = re.compile(
    r"^\s*(?P<address>(?:\d{1,3}\.){3}\d{1,3})\s+(?P<mac>[0-9a-f]{2}(?:-[0-9a-f]{2}){5})\s+(?P<kind>\w+)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LocalNeighbor:
    """A local layer-two neighbor observed by the operating system, not a vendor identity claim."""

    address: str
    mac_address: str
    entry_kind: str


class WindowsArpInventory:
    """Reads the local Windows ARP cache without opening sessions to discovered devices."""

    def parse(self, output: str) -> tuple[LocalNeighbor, ...]:
        """Parse standard Windows ARP output and discard malformed or duplicate entries."""

        neighbors: list[LocalNeighbor] = []
        seen_addresses: set[str] = set()
        for line in output.splitlines():
            match = WINDOWS_ARP_PATTERN.match(line)
            if match is None:
                continue
            address = match.group("address")
            if address in seen_addresses:
                continue
            seen_addresses.add(address)
            neighbors.append(
                LocalNeighbor(
                    address=address,
                    mac_address=match.group("mac").replace("-", ":").lower(),
                    entry_kind=match.group("kind").lower(),
                )
            )
        return tuple(neighbors)

    def collect(self) -> tuple[LocalNeighbor, ...]:
        """Run the Windows local ARP command and return cache evidence without probing neighbors."""

        completed = subprocess.run(
            ["arp", "-a"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.returncode != 0:
            raise RuntimeError("The local ARP inventory command did not complete successfully.")
        return self.parse(completed.stdout)


def authorized_neighbors(
    scope: AuthorizedScope,
    neighbors: Iterable[LocalNeighbor],
    protocol: ManagementProtocol,
) -> tuple[DiscoveryTarget, ...]:
    """Return scope-authorized neighbor targets without storing or resolving any credential value."""

    targets: list[DiscoveryTarget] = []
    for neighbor in neighbors:
        target = DiscoveryTarget(
            address=neighbor.address,
            protocol=protocol,
            credential_reference="local-inventory/no-credential-resolved",
        )
        if scope.authorizes(target):
            targets.append(target)
    return tuple(targets)
