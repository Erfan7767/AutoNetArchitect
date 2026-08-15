from enum import Enum
class ProofStatus(str,Enum):
    VERIFIED="verified"
    PARTIALLY_VERIFIED="partially_verified"
    NOT_VERIFIABLE="not_verifiable_with_current_inputs"
    FAILED="failed"
class EvidenceType(str,Enum):
    FORMAL="formal_verification"
    SIMULATION="simulation"
    ANALYSIS="static_analysis"
