/**
 * Evidence states that determine whether an automated network change may advance.
 * These values intentionally distinguish absence of evidence from a negative result.
 */
export type VirtualValidationState =
  | "not_tested"
  | "test_queued"
  | "test_passed"
  | "test_failed"
  | "test_inconclusive"
  | "not_supported_for_virtual_test";

/** The independently recorded evidence required before a human can release a device change. */
export type ChangeReleaseInput = {
  requirementsComplete: boolean;
  targetFactsCurrent: boolean;
  deviceCapabilityVerified: boolean;
  virtualValidation: VirtualValidationState;
  virtualTestScopeMatches: boolean;
  virtualTestCurrent: boolean;
  backupVerified: boolean;
  maintenanceWindowValid: boolean;
  humanApprovalGranted: boolean;
};

/** A non-destructive release decision that identifies every blocking control. */
export type ChangeReleaseDecision = {
  status: "eligible_for_execution" | "blocked";
  blockers: string[];
};

/** Decision returned before a human approver is asked to release a prepared change. */
export type ApprovalReadinessDecision = {
  status: "ready_for_human_approval" | "blocked";
  blockers: string[];
};

/**
 * Evaluates whether a change is eligible for an already-approved execution path.
 * A passed virtual test is intentionally insufficient on its own.
 */
export function evaluateChangeRelease(input: ChangeReleaseInput): ChangeReleaseDecision {
  const blockers: string[] = [];

  if (!input.requirementsComplete) blockers.push("Requirements are incomplete.");
  if (!input.targetFactsCurrent) blockers.push("Target device facts are missing or stale.");
  if (!input.deviceCapabilityVerified) blockers.push("Target device capability is not verified.");
  if (input.virtualValidation !== "test_passed") blockers.push(`Virtual validation state is ${input.virtualValidation}.`);
  if (!input.virtualTestScopeMatches) blockers.push("Virtual-test scope does not match the requested change.");
  if (!input.virtualTestCurrent) blockers.push("Virtual-test evidence is stale.");
  if (!input.backupVerified) blockers.push("A current backup is not verified.");
  if (!input.maintenanceWindowValid) blockers.push("No valid maintenance window is recorded.");
  if (!input.humanApprovalGranted) blockers.push("A named human approval is required.");

  return blockers.length === 0
    ? { status: "eligible_for_execution", blockers: [] }
    : { status: "blocked", blockers };
}

/**
 * Evaluates the independent controls required before a plan can be presented to
 * a human approver. This function never grants the human approval itself.
 */
export function evaluateApprovalReadiness(
  input: Omit<ChangeReleaseInput, "humanApprovalGranted">,
): ApprovalReadinessDecision {
  const releaseDecision = evaluateChangeRelease({ ...input, humanApprovalGranted: true });
  return releaseDecision.status === "eligible_for_execution"
    ? { status: "ready_for_human_approval", blockers: [] }
    : { status: "blocked", blockers: releaseDecision.blockers };
}

/**
 * Returns a deliberately conservative claim status for user-facing capability language.
 * The platform may only present a positive claim if explicit evidence accompanies it.
 */
export function resolveClaimStatus(evidenceAvailable: boolean): "verified" | "insufficient_evidence" {
  return evidenceAvailable ? "verified" : "insufficient_evidence";
}

/** Claim classes that cannot be presented as factual without scoped evidence. */
export type RestrictedClaimClass =
  | "engineer_equivalence"
  | "production_safe"
  | "compatibility"
  | "compliance";

/** Evidence metadata required to publish a restricted claim. */
export type RestrictedClaimEvidence = {
  claimClass: RestrictedClaimClass;
  scopeDescription: string;
  authorityReference: string;
  measuredEvidenceReference: string;
  reviewedAt: Date | null;
};

/** Result used by API and presentation layers before restricted language is returned. */
export type RestrictedClaimAssessment = {
  status: "publishable" | "blocked";
  missing: string[];
};

/**
 * Checks that a restricted claim is grounded in a defined scope, an authority,
 * measured evidence, and a review timestamp. Generic language is never upgraded
 * to a positive claim merely because an internal workflow completed.
 */
export function assessRestrictedClaim(evidence: RestrictedClaimEvidence): RestrictedClaimAssessment {
  const missing: string[] = [];
  if (!evidence.scopeDescription.trim()) missing.push("A scoped description is required.");
  if (!evidence.authorityReference.trim()) missing.push("An authoritative reference is required.");
  if (!evidence.measuredEvidenceReference.trim()) missing.push("A measured evidence reference is required.");
  if (!evidence.reviewedAt) missing.push("A review timestamp is required.");

  return missing.length === 0 ? { status: "publishable", missing: [] } : { status: "blocked", missing };
}

/** Human responsibilities are intentionally distinct rather than inferred from a login. */
export type HumanAuthority = "reviewer" | "approver" | "executor" | "emergency_authorizer";

/** Inputs required to expose an automation recommendation to a human decision maker. */
export type RecommendationEvidence = {
  sourceFacts: string[];
  rationale: string;
  alternatives: string[];
  affectedDevices: string[];
  unresolvedItems: string[];
  requiredAuthority: HumanAuthority | null;
};

/** A recommendation may be ready for review or must explicitly abstain. */
export type RecommendationAssessment = {
  status: "ready_for_human_review" | "abstain";
  reasons: string[];
};

/**
 * Refuses to elevate an under-evidenced recommendation into an action. The caller
 * must display the returned reasons rather than replace them with guessed values.
 */
export function assessRecommendation(evidence: RecommendationEvidence): RecommendationAssessment {
  const reasons: string[] = [];
  if (evidence.sourceFacts.length === 0) reasons.push("No observed source facts are attached.");
  if (!evidence.rationale.trim()) reasons.push("No engineering rationale is attached.");
  if (evidence.alternatives.length === 0) reasons.push("No alternative has been recorded.");
  if (evidence.affectedDevices.length === 0) reasons.push("No affected-device scope is recorded.");
  if (evidence.unresolvedItems.length > 0) reasons.push("Unresolved evidence or requirement items remain.");
  if (!evidence.requiredAuthority) reasons.push("No required human authority is assigned.");

  return reasons.length === 0
    ? { status: "ready_for_human_review", reasons: [] }
    : { status: "abstain", reasons };
}
