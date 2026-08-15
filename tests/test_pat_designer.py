from designers.nat.pat_designer import PATDesigner
def test_pat_requires_public_ips(): assert PATDesigner().design({"estimated_users":100})["status"]=="blocked_missing_human_data"
