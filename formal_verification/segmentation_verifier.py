from .common import Verifier
from .proof_status import ProofStatus
class SegmentationVerifier(Verifier):
    """Formal/static verification engine."""
    def verify(self,r):
        boundaries=r.get("segmentation_boundaries");observed=r.get("observed_paths");
        if boundaries is None or observed is None:return self.result(ProofStatus.NOT_VERIFIABLE,[],["segmentation boundary or observed paths unavailable"],source_of_truth=r.get("source_of_truth","requirements_document"))
        leaks=[p for p in observed if p.get("crosses_boundary") and not p.get("allowed")];return self.result(ProofStatus.FAILED if leaks else ProofStatus.VERIFIED,["segmentation boundaries respected"] if not leaks else [],leaks,source_of_truth=r.get("source_of_truth","requirements_document"),evidence=["formal_segmentation_check"])
