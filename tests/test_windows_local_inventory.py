"""Tests for local Windows ARP inventory parsing and scope filtering."""

from __future__ import annotations

from site_agent.local_inventory import WindowsArpInventory, authorized_neighbors
from site_agent.models import ManagementProtocol
from site_agent.scope import AuthorizedScope


def test_windows_arp_inventory_parses_neighbors_without_claiming_vendor_identity() -> None:
    """The collector records only ARP evidence and ignores non-entry output lines."""

    output = """Interface: 192.0.2.5 --- 0x6
  Internet Address      Physical Address      Type
  192.0.2.10            00-11-22-33-44-55     dynamic
  192.0.2.11            aa-bb-cc-dd-ee-ff     static
"""
    entries = WindowsArpInventory().parse(output)
    assert [(entry.address, entry.mac_address, entry.entry_kind) for entry in entries] == [
        ("192.0.2.10", "00:11:22:33:44:55", "dynamic"),
        ("192.0.2.11", "aa:bb:cc:dd:ee:ff", "static"),
    ]


def test_authorized_neighbors_requires_consent_network_protocol_and_target_allowlist() -> None:
    """ARP entries remain non-actionable until every scope control authorizes the address."""

    entries = WindowsArpInventory().parse(
        "192.0.2.10 00-11-22-33-44-55 dynamic\n192.0.2.11 aa-bb-cc-dd-ee-ff dynamic"
    )
    scope = AuthorizedScope(
        site_id="lab-arp",
        approved_networks=("192.0.2.0/24",),
        approved_targets=("192.0.2.10",),
        allowed_protocols=(ManagementProtocol.SSH,),
        approval_reference="LAB-ARP-01",
        operator_acknowledged=True,
    )
    targets = authorized_neighbors(scope, entries, ManagementProtocol.SSH)
    assert [target.address for target in targets] == ["192.0.2.10"]
