from verification.post_deploy_verifier import PostDeployVerifier


def _identity():
    return {"vendor": "cisco", "platform": "ios_xe", "model": "C9300", "version": "17.9.4", "serial": "FDO123", "hostname": "core-1", "status": "collected", "confidence": "high", "evidence_hash": "e1"}


def test_post_deploy_verifier_allows_only_complete_verified_evidence():
    report = PostDeployVerifier().verify({"asset-1": _identity()}, {"asset-1": _identity()}, {"asset-1": {"healthy": True, "evidence_ids": ["op-1"]}})
    assert report.proof_status == "verified"
    assert report.production_suitable is True
    assert report.deployment_gate == "allow"


def test_post_deploy_verifier_blocks_missing_runtime_and_identity_drift():
    missing = PostDeployVerifier().verify({"asset-1": _identity()}, {"asset-1": _identity()})
    assert missing.production_suitable is False
    assert missing.proof_status == "not_verifiable_with_current_inputs"
    drifted = {**_identity(), "model": "C9300-48"}
    failed = PostDeployVerifier().verify({"asset-1": _identity()}, {"asset-1": drifted}, {"asset-1": {"healthy": True}})
    assert failed.proof_status == "failed"
    assert failed.deployment_gate == "block_or_review"
