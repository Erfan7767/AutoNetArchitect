from dataclasses import replace

from firmware import FirmwareImage, FirmwareManager, FirmwareTarget, FirmwareUpgradeRequest, UpgradePath, UpgradePlanner
from firmware.firmware_manager import BootMode


def _image(image_id, version):
    return FirmwareImage(image_id, "cisco", "ios_xe", "C9300-48P", version, "a" * 64, artifact_reference=f"artifact://{image_id}", boot_mode=BootMode.INSTALL.value, evidence_ids=(f"ev-{image_id}",))


def _target(target_id, group):
    return FirmwareTarget(target_id, target_id, "cisco", "ios_xe", "C9300-48P", "17.6.5", BootMode.INSTALL.value, group, "member", management_reference=f"oob://{target_id}")


def _request(request_id, target, image, path_id):
    return FirmwareUpgradeRequest(request_id, target, image, upgrade_path_id=path_id, dry_run=True, evidence_ids=(f"ev-{request_id}",))


def _manager():
    manager = FirmwareManager()
    for image_id, version in (("IMG-1", "17.9.4"), ("IMG-2", "17.9.4"), ("IMG-3", "17.9.4")):
        manager.register_image(_image(image_id, version))
    manager.register_upgrade_path(UpgradePath("PATH-1", "cisco", "ios_xe", "C9300-48P", "17.6.5", "17.9.4", BootMode.INSTALL.value, BootMode.INSTALL.value, "supported", "ROLLBACK", ("ev-path-1",)))
    return manager


def test_upgrade_planner_separates_members_of_same_redundancy_group():
    manager = _manager()
    requests = (_request("REQ-1", _target("edge-a", "PAIR-1"), manager.images["IMG-1"], "PATH-1"), _request("REQ-2", _target("edge-b", "PAIR-1"), manager.images["IMG-2"], "PATH-1"), _request("REQ-3", _target("edge-c", "PAIR-2"), manager.images["IMG-3"], "PATH-1"))
    plan = UpgradePlanner(manager).plan(requests, plan_id="PLAN-1", canary_request_ids=("REQ-1",))
    assert plan.allowed is True
    assert len(plan.stages) == 2
    assert set(plan.stages[0].request_ids) != {"REQ-1", "REQ-2"}
    assert plan.stages[0].canary is True
    assert all(len(stage.redundancy_groups) == len(set(stage.redundancy_groups)) for stage in plan.stages)


def test_upgrade_planner_requires_prior_stage_completion():
    manager = _manager()
    requests = (_request("REQ-1", _target("edge-a", "PAIR-1"), manager.images["IMG-1"], "PATH-1"), _request("REQ-2", _target("edge-b", "PAIR-1"), manager.images["IMG-2"], "PATH-1"))
    plan = UpgradePlanner(manager).plan(requests)
    allowed, reasons = UpgradePlanner(manager).validate_stage(plan, 2)
    assert allowed is False
    assert "prior stage 1 is incomplete" in reasons[0]
    allowed_after, reasons_after = UpgradePlanner(manager).validate_stage(plan, 2, ("REQ-1",))
    assert allowed_after is True
    assert reasons_after == ()


def test_upgrade_planner_blocks_unregistered_exact_path():
    manager = FirmwareManager()
    manager.register_image(_image("IMG-1", "17.9.4"))
    request = _request("REQ-1", _target("edge-a", "PAIR-1"), manager.images["IMG-1"], "PATH-MISSING")
    plan = UpgradePlanner(manager).plan((request,))
    assert plan.allowed is False
    assert "exact_upgrade_path:REQ-1" in plan.required_human_inputs
