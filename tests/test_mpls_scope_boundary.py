from designers.mpls.mpls_scope_boundary import MPLSScopeBoundary
def test_sp_side_out_scope(): assert "pe_configuration" in MPLSScopeBoundary().design({})["out_of_scope"]
