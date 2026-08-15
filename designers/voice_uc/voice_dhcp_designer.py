from designers.voice_uc.common import VoiceDesigner
class VoiceDHCPDesigner(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        missing=self.mandatory(r,["tftp_server"]);self.record_decision("voice_dhcp",r.get("voice_vlans",[]),"phone DHCP scope carries gateway, DNS, and provisioning options");return {"status":"blocked_missing_human_data" if missing else "designed","scopes":r.get("voice_vlans",[]),"options":{"150":r.get("tftp_server"),"66":r.get("tftp_server"),"43":r.get("option_43"),"242":r.get("option_242")},"lease_hours":r.get("lease_hours",12),"decisions":self.decisions,"assumptions":self.assumptions}
