from domain_packs.university_campus.multicast_video_profile import MulticastVideoProfile

def test_multicast_video_profile_imports_and_scope():
    result = MulticastVideoProfile().design({"sector": "university_campus"})
    assert result["scope_guard"]["applicable"] is True
