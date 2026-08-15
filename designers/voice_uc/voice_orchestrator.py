from designers.voice_uc.common import VoiceDesigner
from .voice_strategy_selector import VoiceStrategySelector
from .voice_vlan_designer import VoiceVLANDesigner
from .voice_qos_designer import VoiceQoSDesigner
from .voice_bandwidth_calculator import VoiceBandwidthCalculator
from .voice_scope_boundary import VoiceScopeBoundary
class VoiceOrchestrator(VoiceDesigner):
    """Assemble VoiceNetworkDesign without designing the UC platform itself."""
    def design(self,r):
        scope=VoiceScopeBoundary().design(r);strategy=VoiceStrategySelector().design(r);required=bool(r.get("voice_required",True));parts={"scope":scope,"strategy":strategy}
        if required:parts.update({"vlan":VoiceVLANDesigner().design(r),"qos":VoiceQoSDesigner().design(r),"bandwidth":VoiceBandwidthCalculator().design(r)})
        self.record_decision("voice_orchestration",required,"network support artifact is assembled only for requested voice service");return {"artifact":"VoiceNetworkDesign","required":required,"parts":parts,"decisions":self.decisions}
