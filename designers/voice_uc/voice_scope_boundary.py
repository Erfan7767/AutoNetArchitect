from designers.voice_uc.common import VoiceDesigner
class VoiceScopeBoundary(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        in_scope=["voice_vlans","voice_qos","voice_bandwidth","voice_security","voice_dhcp","gateway_network_placement","survivability"];out_scope=["uc_application_configuration","dial_plan","voicemail","ivr","contact_center","uc_user_provisioning","sip_provider_negotiation"];self.record_decision("voice_scope",in_scope,"designer supports network infrastructure, not UC application administration");return {"in_scope":in_scope,"out_of_scope":out_scope,"status":"bounded","human_supplied_out_scope":True,"decisions":self.decisions}
