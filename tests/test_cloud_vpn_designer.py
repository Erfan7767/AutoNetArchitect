from designers.cloud.cloud_vpn_designer import CloudVPNDesigner
def test_cloud_details_mandatory(): assert CloudVPNDesigner().design({})["status"]=="blocked_missing_human_data"
