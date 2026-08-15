from designers.dr_bc.dr_scope_boundary import DRScopeBoundary
def test_application_out_scope(): assert "application_dr" in DRScopeBoundary().design({})['out_of_scope']
