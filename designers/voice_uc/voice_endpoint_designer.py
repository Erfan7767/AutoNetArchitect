from designers.voice_uc.common import VoiceDesigner
class VoiceEndpointDesigner(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        types=r.get("endpoint_types",["desk_phone"]);poe={"desk_phone":15,"conference_room":30,"analog_adapter":7,"paging":7};total=sum(poe.get(t,15)*int(r.get("counts",{}).get(t,0)) for t in types);ports=sum(int(r.get("counts",{}).get(t,0)) for t in types);self.record_decision("voice_endpoints",types,"endpoint type determines PoE, port, and QoS requirements");return {"types":types,"poe_watts":total,"ports":ports,"cdp_lldp":True,"decisions":self.decisions}
