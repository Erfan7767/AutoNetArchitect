from designers.voice_uc.voice_scope_boundary import VoiceScopeBoundary
def test_uc_out_of_scope(): assert "dial_plan" in VoiceScopeBoundary().design({})["out_of_scope"]
