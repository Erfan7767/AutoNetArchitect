from designers.voice_uc.common import VoiceDesigner
class VoiceSecurityDesigner(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        self.record_decision("voice_security",True,"voice VLAN isolation, encrypted signaling/media, and explicit firewall ranges");return {"voice_vlan_isolation":True,"sip_tls":r.get("sip_tls",True),"srtp":r.get("srtp",True),"sip_alg":"disable_with_review","ports":{"sip":[5060,5061],"rtp":"16384-32767","sccp":[2000,2443],"h323":[1720],"mgcp":[2427,2727]},"decisions":self.decisions}
