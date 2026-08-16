"""Typed, secret-free records exchanged by an authorized site agent."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ManagementProtocol(str, Enum):
    """Read-only management channels that may be authorized by a site scope."""

    HTTPS_API = "https_api"
    NETCONF = "netconf"
    SNMP = "snmp"
    SSH = "ssh"


class DiscoveryState(str, Enum):
    """Outcome state for a single discovery attempt."""

    DISCOVERED = "discovered"
    UNREACHABLE = "unreachable"
    UNAUTHORIZED = "unauthorized"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"


class VirtualTestState(str, Enum):
    """Evidence state of a virtual validation result."""

    NOT_TESTED = "not_tested"
    TEST_QUEUED = "test_queued"
    TEST_PASSED = "test_passed"
    TEST_FAILED = "test_failed"
    TEST_INCONCLUSIVE = "test_inconclusive"
    NOT_SUPPORTED_FOR_VIRTUAL_TEST = "not_supported_for_virtual_test"


class DiscoveryTarget(BaseModel):
    """A single approved management endpoint with no credential material."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    address: str = Field(min_length=1, max_length=255)
    protocol: ManagementProtocol
    credential_reference: str = Field(min_length=1, max_length=160)


class ObservedDeviceFacts(BaseModel):
    """Read-only facts reported by a collector when it can identify a device."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vendor: str = Field(min_length=1, max_length=120)
    platform: str = Field(min_length=1, max_length=160)
    software_version: str = Field(min_length=1, max_length=160)
    serial_reference: str = Field(min_length=1, max_length=200)
    interface_count: int = Field(ge=0)
    capabilities: tuple[str, ...] = ()


class DiscoveryResult(BaseModel):
    """Secret-free discovery evidence for a target attempted by the site agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target: DiscoveryTarget
    state: DiscoveryState
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    facts: ObservedDeviceFacts | None = None
    message: str = Field(min_length=1, max_length=500)


class VirtualTestResult(BaseModel):
    """A scope-labelled test result used by the control plane release gate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    state: VirtualTestState
    adapter_kind: str = Field(min_length=1, max_length=120)
    fidelity_label: str = Field(min_length=1, max_length=120)
    artifact_hash: str = Field(min_length=1, max_length=160)
    target_facts_hash: str = Field(min_length=1, max_length=160)
    scope_hash: str = Field(min_length=1, max_length=160)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    detail: str = Field(min_length=1, max_length=1000)


class AgentHealth(BaseModel):
    """Non-sensitive health record proving the agent is available for assigned work."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_id: str = Field(min_length=1, max_length=160)
    site_id: str = Field(min_length=1, max_length=160)
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: str = "read_only"
    healthy: bool
    detail: str = Field(min_length=1, max_length=500)
