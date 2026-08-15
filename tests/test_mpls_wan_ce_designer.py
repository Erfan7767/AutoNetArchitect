from designers.mpls.mpls_wan_ce_designer import MPLSWANCEDesigner
def test_sp_fields_mandatory(): assert MPLSWANCEDesigner().design({})["status"]=="blocked_missing_human_data"
