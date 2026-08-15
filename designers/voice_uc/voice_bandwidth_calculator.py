from designers.voice_uc.common import VoiceDesigner
class VoiceBandwidthCalculator(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        codec=r.get("codec","G711_ulaw");table={"G711_ulaw":87,"G711_alaw":87,"G729":31,"Opus":64,"SILK":52};per=table.get(codec,87);calls=int(r.get("concurrent_calls",0));total=per*calls;self.record_decision("voice_bandwidth",total,"codec table plus concurrent call count determines capacity");return {"codec":codec,"kbps_per_call":per,"concurrent_calls":calls,"total_kbps":total,"upgrade_required":total>r.get("link_kbps",10**9),"decisions":self.decisions}
