from datetime import datetime, timezone

from site_agent.models import DiscoveryResult, DiscoveryState, DiscoveryTarget, ManagementProtocol, ObservedDeviceFacts
from windows_app.inventory_review import InventoryDisposition, summarize_inventory


def target(address: str) -> DiscoveryTarget:
    return DiscoveryTarget(address=address, protocol=ManagementProtocol.SSH, credential_reference="credential-ref")


def test_discovered_rows_preserve_observed_facts_as_evidence() -> None:
    result = DiscoveryResult(
        target=target("192.0.2.10"),
        state=DiscoveryState.DISCOVERED,
        collected_at=datetime.now(timezone.utc),
        facts=ObservedDeviceFacts(
            vendor="Cisco",
            platform="ios_xe",
            software_version="17.9.4",
            serial_reference="serial-ref",
            interface_count=24,
        ),
        message="Observed identity and version evidence.",
    )
    summary = summarize_inventory([result])
    row = summary.rows[0]
    assert row.disposition is InventoryDisposition.EVIDENCE_RECORDED
    assert row.requires_human_review is False
    assert row.vendor == "Cisco"
    assert summary.all_targets_reviewed is True


def test_ambiguous_and_unsupported_rows_abstain_without_facts() -> None:
    results = [
        DiscoveryResult(target=target("192.0.2.11"), state=DiscoveryState.AMBIGUOUS, message="Identity evidence is ambiguous."),
        DiscoveryResult(target=target("192.0.2.12"), state=DiscoveryState.UNSUPPORTED, message="Vendor family is not supported."),
    ]
    summary = summarize_inventory(results)
    assert summary.abstained_count == 2
    assert summary.unresolved_count == 2
    assert summary.all_targets_reviewed is False
    assert all(row.vendor is None and row.platform is None and row.software_version is None for row in summary.rows)


def test_unauthorized_and_unreachable_are_human_review_items() -> None:
    results = [
        DiscoveryResult(target=target("192.0.2.13"), state=DiscoveryState.UNAUTHORIZED, message="Authorization was not recorded."),
        DiscoveryResult(target=target("192.0.2.14"), state=DiscoveryState.UNREACHABLE, message="Target did not respond."),
    ]
    summary = summarize_inventory(results)
    assert {row.disposition for row in summary.rows} == {InventoryDisposition.UNAUTHORIZED, InventoryDisposition.UNREACHABLE}
    assert all(row.requires_human_review for row in summary.rows)
    assert summary.state_counts[DiscoveryState.UNAUTHORIZED.value] == 1
