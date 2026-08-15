from designers.voice_uc.common import VoiceDesigner
class VoiceVLANDesigner(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        vlans=r.get("voice_vlans",[]);self.record_decision("voice_vlans",vlans,"voice VLANs align with VLAN, IP, DHCP, and FHRP plans");return {"vlans":vlans,"dhcp_required":True,"fhrp_required":True,"access_port_voice_vlan":True,"decisions":self.decisions}
