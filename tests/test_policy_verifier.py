from formal_verification.policy_verifier import PolicyVerifier
def test_policy_unavailable(): assert PolicyVerifier().verify({})["proof_status"]=="not_verifiable_with_current_inputs"
