"""Tests for vendor-specific read-only discovery plan contracts."""

import pytest

from site_agent.discovery_adapters import (
    CiscoDiscoveryAdapter,
    FortinetDiscoveryAdapter,
    HpeArubaDiscoveryAdapter,
    HuaweiDiscoveryAdapter,
)
from site_agent.models import DiscoveryTarget, ManagementProtocol


def target(protocol: ManagementProtocol) -> DiscoveryTarget:
    """Build a secret-free target using a reference rather than credentials."""

    return DiscoveryTarget(address="192.0.2.10", protocol=protocol, credential_reference="cred-ref-1")


@pytest.mark.parametrize(
    ("adapter_type", "protocol"),
    (
        (CiscoDiscoveryAdapter, ManagementProtocol.NETCONF),
        (HuaweiDiscoveryAdapter, ManagementProtocol.NETCONF),
        (FortinetDiscoveryAdapter, ManagementProtocol.HTTPS_API),
        (HpeArubaDiscoveryAdapter, ManagementProtocol.HTTPS_API),
    ),
)
def test_vendor_adapter_creates_read_only_plan(adapter_type: type, protocol: ManagementProtocol) -> None:
    """Each official vendor adapter emits evidence requests marked read-only."""

    plan = adapter_type().plan(target(protocol))

    assert plan.execution_mode == "read_only_only"
    assert plan.requests
    assert all(request.read_only for request in plan.requests)
    assert all(request.credential_reference == "cred-ref-1" for request in plan.requests)
    assert all(request.required_evidence[0].startswith("discovery.") for request in plan.requests)


def test_fortinet_plan_contains_vendor_specific_vdom_evidence() -> None:
    """Fortinet VDOM context is explicit instead of being silently inferred."""

    plan = FortinetDiscoveryAdapter().plan(target(ManagementProtocol.HTTPS_API))

    assert "discovery.virtual_domains_summary" in {request.required_evidence[0] for request in plan.requests}


def test_adapter_rejects_unsupported_protocol() -> None:
    """The adapter rejects a protocol outside the vendor contract before any collection."""

    with pytest.raises(ValueError, match="not supported"):
        CiscoDiscoveryAdapter().plan(target(ManagementProtocol.SNMP))
