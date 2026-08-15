from change_management import ChangeExport, ChangeRequest


def test_change_export_supports_local_and_external_ready_formats():
    request = ChangeRequest("CHG-28", "Export", "Detailed", "alice")
    exporter = ChangeExport()
    assert '"change_id": "CHG-28"' in exporter.json(request)
    assert "change_id" in exporter.csv([request]).splitlines()[0]
    assert exporter.pdf(request).startswith(b"%PDF")
    assert exporter.external(request, "servicenow")["u_autonetarchitect_change_id"] == "CHG-28"
    assert exporter.external(request, "jira")["external_id"] == "CHG-28"
    assert exporter.external(request, "generic")["external_integration_required"] is True
