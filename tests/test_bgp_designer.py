from designers.wan.bgp_designer import BGPDesigner
def test_bgp_requires_authority(): assert BGPDesigner().design({})["status"]=="blocked_missing_human_data"
