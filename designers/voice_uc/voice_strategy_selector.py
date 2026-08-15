from designers.voice_uc.common import VoiceDesigner
class VoiceStrategySelector(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        missing=self.mandatory(r,["uc_platform"]);platform=str(r.get("uc_platform","" )).lower();
        strategy="hybrid" if r.get("hybrid") else "cloud" if any(x in platform for x in ["teams","zoom","ringcentral"]) else "on_prem";self.record_decision("voice_strategy",strategy,"UC platform and migration intent select network strategy");return {"status":"blocked_missing_human_data" if missing else "designed","strategy":strategy,"platform":r.get("uc_platform"),"pstn":r.get("pstn_required",False),"decisions":self.decisions,"assumptions":self.assumptions}
