from designers.voice_uc.common import VoiceDesigner
class VoiceGatewayDesigner(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        missing=self.mandatory(r,["gateway_type"]);self.record_decision("voice_gateway",r.get("gateway_type"),"gateway/SBC placement and media ranges are explicit");return {"status":"blocked_missing_human_data" if missing else "designed","gateway_type":r.get("gateway_type"),"placement":r.get("placement","dmz"),"signaling_ports":[5060,5061],"media_range":"16384-32767","decisions":self.decisions,"assumptions":self.assumptions}
