import { assessRestrictedClaim, type RestrictedClaimEvidence } from "./automationPolicy";
import { RESTRICTED_CLAIM_PRESENTATION, type RestrictedClaimPresentationId } from "../shared/claimPresentation";

export type RestrictedClaimReportEntry = {
  claimClass: RestrictedClaimPresentationId;
  label: string;
  status: "publishable" | "blocked";
  blockers: string[];
  requirement: string;
};

type StoredClaimEvidence = RestrictedClaimEvidence & { assessmentStatus?: "publishable" | "blocked" };

/** Builds a report-safe claim summary without emitting a factual product claim. */
export function buildRestrictedClaimReport(evidence: StoredClaimEvidence[]): RestrictedClaimReportEntry[] {
  return RESTRICTED_CLAIM_PRESENTATION.map(definition => {
    const supplied = evidence.find(item => item.claimClass === definition.id);
    if (!supplied) {
      return {
        claimClass: definition.id,
        label: definition.label,
        status: "blocked" as const,
        blockers: ["No scoped evidence record has been supplied for this restricted claim class."],
        requirement: definition.requirement,
      };
    }
    const assessment = assessRestrictedClaim(supplied);
    const blockedByRecordedAssessment = supplied.assessmentStatus === "blocked";
    return {
      claimClass: definition.id,
      label: definition.label,
      status: blockedByRecordedAssessment ? "blocked" : assessment.status,
      blockers: blockedByRecordedAssessment && assessment.missing.length === 0 ? ["The recorded scoped claim assessment remains blocked for additional measured-coverage or review controls."] : assessment.missing,
      requirement: definition.requirement,
    };
  });
}
