"""Tests for the pure Windows vendor-support review presenter."""

from site_agent.models import ManagementProtocol
from windows_app.vendor_support_view import protocol_allowed, support_rows


def test_support_rows_are_secret_free_and_bounded() -> None:
    """The local review surface exposes four families and no version claim."""

    rows = support_rows()

    assert {row.vendor_family for row in rows} == {"cisco", "huawei", "fortinet", "hpe_aruba"}
    assert all(row.configuration_status == "verification_required" for row in rows)
    assert all(row.version_policy_status == "not_loaded" for row in rows)
    assert all("evidence" in row.boundary for row in rows)


def test_protocol_guard_is_vendor_specific() -> None:
    """Protocol selection is rejected when it is outside the selected family contract."""

    assert protocol_allowed("cisco", ManagementProtocol.NETCONF)
    assert protocol_allowed("fortinet", ManagementProtocol.HTTPS_API)
    assert not protocol_allowed("fortinet", ManagementProtocol.NETCONF)
    assert not protocol_allowed("unknown", ManagementProtocol.SSH)


def test_windows_app_discovery_path_blocks_protocol_mismatch(monkeypatch) -> None:
    """The actual app method blocks a mismatched selected-vendor protocol before collector use."""

    pytest = __import__("pytest")
    pytest.importorskip("tkinter")
    from site_agent.vendor_support import VendorCapabilityRegistry, VendorFamily
    from windows_app.app import AutoNetWindowsApp

    class FakeVar:
        def __init__(self, value: str) -> None:
            self.value = value

        def get(self) -> str:
            return self.value

    app = AutoNetWindowsApp.__new__(AutoNetWindowsApp)
    app._vendor_family = FakeVar(VendorFamily.FORTINET.value)
    app._protocol = FakeVar(ManagementProtocol.NETCONF.value)
    app._address = FakeVar("192.0.2.10")
    app._credential_reference = FakeVar("cred-ref-1")
    app._vendor_contracts = {contract.family.value: contract for contract in VendorCapabilityRegistry().contracts}
    app._status = FakeVar("")
    app._controller = object()
    errors: list[str] = []
    monkeypatch.setattr("windows_app.app.messagebox.showerror", lambda _title, message: errors.append(str(message)))

    app._discover()

    assert errors
    assert "not declared" in errors[0]
