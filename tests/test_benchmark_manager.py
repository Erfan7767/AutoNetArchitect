from benchmarking.benchmark_manager import BenchmarkManager, BenchmarkObservation
from benchmarking.engineer_baseline import EngineerBaseline, EngineerBaselineRegistry

def test_benchmark_manager_creates_repeatable_run_and_records_observation():
    baselines = EngineerBaselineRegistry((EngineerBaseline(baseline_id="b-1", scenario_id="greenfield-campus", engineer_reference="human://b-1", review_status="validated"),))
    manager = BenchmarkManager(baselines=baselines)
    run = manager.start_run("run-1")
    manager.record_observation("run-1", BenchmarkObservation(observation_id="obs-1", scenario_id="greenfield-campus", engineer_baseline_id="b-1", actual_outcome="reviewed", evidence_ids=("ev-1",)))
    final = manager.finalize("run-1")
    assert final.status == "finalized" and final.corpus_fingerprint and final.repeatability_key and len(manager.observations("run-1")) == 1

def test_benchmark_manager_rejects_unknown_scenario():
    manager = BenchmarkManager()
    manager.start_run("run-unknown")
    try:
        manager.record_observation("run-unknown", BenchmarkObservation(observation_id="obs-x", scenario_id="not-in-corpus"))
    except KeyError:
        return
    raise AssertionError("unknown scenario was accepted")
