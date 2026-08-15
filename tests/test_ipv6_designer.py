from designers.ip.ipv6_designer import IPv6Designer
def test_ipv6_requires_prefix(): assert IPv6Designer().design({})["status"]=="blocked_missing_human_data"
