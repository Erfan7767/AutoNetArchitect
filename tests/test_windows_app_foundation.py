"""Tests for the secret-free Windows discovery foundation."""

from __future__ import annotations

from pathlib import Path

import pytest

from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol
from site_agent.scope import AuthorizedScope
from windows_app.controller import WindowsDiscoveryController
from windows_app.workspace import WindowsWorkspace


def test_windows_controller_blocks_discovery_without_saved_scope(tmp_path: Path) -> None:
    """Discovery cannot run merely because a target is typed into the desktop application."""

    controller = WindowsDiscoveryController(
        WindowsWorkspace(tmp_path),
        lambda target: DiscoveryResult(target=target, state=DiscoveryState.DISCOVERED, message="Test collector."),
    )
    target = DiscoveryTarget(address="192.0.2.10", protocol=ManagementProtocol.SSH, credential_reference="secret://device/admin")
    with pytest.raises(PermissionError, match="approved local scope"):
        controller.discover_target(target)


def test_windows_controller_preserves_scope_and_denies_out_of_scope_target(tmp_path: Path) -> None:
    """The workspace persists approval metadata and blocks a target outside its approved network."""

    workspace = WindowsWorkspace(tmp_path)
    controller = WindowsDiscoveryController(
        workspace,
        lambda target: DiscoveryResult(target=target, state=DiscoveryState.DISCOVERED, message="Test collector."),
    )
    controller.approve_scope(
        AuthorizedScope(
            site_id="lab-01",
            approved_networks=("192.0.2.0/24",),
            approved_targets=("192.0.2.10",),
            allowed_protocols=(ManagementProtocol.SSH,),
            approval_reference="LAB-APPROVAL-01",
            operator_acknowledged=True,
        )
    )
    result = controller.discover_target(
        DiscoveryTarget(address="198.51.100.10", protocol=ManagementProtocol.SSH, credential_reference="secret://device/admin")
    )
    assert workspace.load_scope() is not None
    assert result.state is DiscoveryState.UNAUTHORIZED


def test_windows_controller_blocks_target_inside_cidr_when_not_on_target_allowlist(tmp_path: Path) -> None:
    """A CIDR entry alone never authorizes a target excluded by the explicit target list."""

    controller = WindowsDiscoveryController(
        WindowsWorkspace(tmp_path),
        lambda target: DiscoveryResult(target=target, state=DiscoveryState.DISCOVERED, message="Test collector."),
    )
    controller.approve_scope(
        AuthorizedScope(
            site_id="lab-02",
            approved_networks=("192.0.2.0/24",),
            approved_targets=("192.0.2.10",),
            allowed_protocols=(ManagementProtocol.SSH,),
            approval_reference="LAB-APPROVAL-02",
            operator_acknowledged=True,
        )
    )
    result = controller.discover_target(
        DiscoveryTarget(address="192.0.2.11", protocol=ManagementProtocol.SSH, credential_reference="secret://device/admin")
    )
    assert result.state is DiscoveryState.UNAUTHORIZED


def test_windows_controller_rejects_scope_without_operator_acknowledgement(tmp_path: Path) -> None:
    """A scope must include explicit local consent before it can be saved for discovery."""

    controller = WindowsDiscoveryController(
        WindowsWorkspace(tmp_path),
        lambda target: DiscoveryResult(target=target, state=DiscoveryState.DISCOVERED, message="Test collector."),
    )
    with pytest.raises(PermissionError, match="explicitly acknowledge"):
        controller.approve_scope(
            AuthorizedScope(
                site_id="lab-03",
                approved_networks=("192.0.2.0/24",),
                approved_targets=("192.0.2.10",),
                allowed_protocols=(ManagementProtocol.SSH,),
                approval_reference="LAB-APPROVAL-03",
            )
        )
