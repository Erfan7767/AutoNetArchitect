from pathlib import Path
import tempfile

from source_of_truth.sot_manager import SoTConflictError, SoTManager, SoTNotFoundError, SoTType


def test_sot_manager_enforces_four_governed_types():
    with tempfile.TemporaryDirectory() as directory:
        manager = SoTManager(Path(directory) / "sot.json")
        records = {}
        for sot_type in SoTType:
            record = manager.register(sot_type, {"domain": sot_type.value.lower()}, "architect", "approved-design-document", (f"evidence-{sot_type.value}",), approved=True)
            records[sot_type.value] = record
        resolved = manager.require(tuple(SoTType))
        assert set(resolved) == {item.value for item in SoTType}
        assert manager.verify_integrity()


def test_sot_manager_blocks_missing_and_conflicting_authority():
    with tempfile.TemporaryDirectory() as directory:
        manager = SoTManager(Path(directory) / "sot.json")
        try:
            manager.authoritative(SoTType.DESIGN)
        except SoTNotFoundError:
            pass
        else:
            raise AssertionError("missing SoT must block resolution")
        manager.register(SoTType.DESIGN, {"version": 1}, "a", "source-a", approved=True)
        manager.register(SoTType.DESIGN, {"version": 2}, "b", "source-b", approved=True)
        try:
            manager.authoritative(SoTType.DESIGN)
        except SoTConflictError:
            return
        raise AssertionError("multiple approved SoT records must block resolution")
