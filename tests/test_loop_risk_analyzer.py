from formal_verification.loop_risk_analyzer import LoopRiskAnalyzer
def test_cycle_failed(): assert LoopRiskAnalyzer().verify({"edges":[["a","b"],["b","a"]]})["proof_status"]=="failed"
