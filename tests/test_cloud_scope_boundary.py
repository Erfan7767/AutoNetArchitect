from designers.cloud.cloud_scope_boundary import CloudScopeBoundary
def test_scope_bounded(): assert "cloud_vpc_vnet_internal_design" in CloudScopeBoundary().design({})["out_of_scope"]
