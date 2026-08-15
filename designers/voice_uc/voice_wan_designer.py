from designers.voice_uc.common import VoiceDesigner
class VoiceWANDesigner(VoiceDesigner):
    """Voice network design engine."""
    def design(self,r):
        self.record_decision("voice_wan",r.get("max_calls",0),"CAC, delay, loss, and jitter guard voice quality");return {"bandwidth_reservation_percent":r.get("reservation_percent",20),"max_concurrent_calls":r.get("max_calls"),"cac":"block_or_local_pstn_overflow","one_way_delay_ms":150,"round_trip_delay_ms":300,"packet_loss_percent":1,"jitter_buffer":"adaptive","decisions":self.decisions}
