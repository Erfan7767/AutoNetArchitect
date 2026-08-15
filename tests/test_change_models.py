from datetime import datetime, timezone

from change_management import ChangeRequest, ChangeStatus, ConfigChange, DeviceRef, ImplementationPlan, RollbackPlan


def test_change_models_serialize_complete_request_contract():
    request = ChangeRequest("CHG-20260101-0001", "Add VLAN", "Create one documented VLAN", "alice", affected_devices=[DeviceRef("edge-1", "edge-1", "cisco", "ios_xe")], config_changes=[ConfigChange("edge-1", "edge-1", "vlan", "", "vlan 20", "diff", ("vlan 20",), ("no vlan 20",))], implementation_plan=ImplementationPlan(), rollback_plan=RollbackPlan())
    data = request.to_dict()
    assert data["change_id"].startswith("CHG-")
    assert data["status"] == ChangeStatus.DRAFT.value
    assert data["affected_devices"][0]["device_id"] == "edge-1"
    assert data["config_changes"][0]["commands_to_apply"] == ["vlan 20"]
