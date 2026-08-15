from designers.voice_uc.common import VoiceDesigner
class VoiceQoSDesigner(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        policy={"bearer":"EF/46","signaling":"CS3/24","video":"AF41/34","priority_queue":True,"trust_phone":True,"trust_pc":False,"llq_wan":True,"police_priority":True};self.record_decision("voice_qos",policy,"voice bearer receives EF and strict priority with bounded policing");return {"policy":policy,"bandwidth_reservation_percent":r.get("voice_reservation_percent",20),"decisions":self.decisions}
