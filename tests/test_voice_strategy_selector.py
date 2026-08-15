from designers.voice_uc.voice_strategy_selector import VoiceStrategySelector
def test_platform_mandatory(): assert VoiceStrategySelector().design({})["status"]=="blocked_missing_human_data"
