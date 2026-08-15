from designers.voice_uc.voice_dhcp_designer import VoiceDHCPDesigner
def test_tftp_mandatory(): assert VoiceDHCPDesigner().design({})["status"]=="blocked_missing_human_data"
