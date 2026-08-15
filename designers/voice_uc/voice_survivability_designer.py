from designers.voice_uc.common import VoiceDesigner
class VoiceSurvivabilityDesigner(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        sites=r.get("sites",[]);plans=[{"site":s,"strategy":r.get("strategy","srst_or_local_gateway"),"local_pstn":True,"emergency_during_outage":True} for s in sites];self.record_decision("voice_survivability",plans,"branch survivability protects calling during WAN loss");return {"plans":plans,"decisions":self.decisions}
