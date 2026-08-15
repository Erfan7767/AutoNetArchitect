from incident_response.incident_export import IncidentExporter

def test_incident_export_supports_json_csv_and_itsm_without_submission():
    exporter = IncidentExporter()
    payload = {"incident_id":"INC-20260814-0001", "title":"Issue", "description":"Issue", "severity":"P3"}
    assert "incident_id" in exporter.to_json(payload)
    assert "incident_id" in exporter.to_csv([payload])
    itsm = exporter.to_itsm(payload, system="jira")
    assert itsm["external_submission"] is False
