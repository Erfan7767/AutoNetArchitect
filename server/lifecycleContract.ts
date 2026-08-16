/**
 * A read-only lifecycle assessment. It coordinates evidence already stored by
 * the control plane and never starts discovery, configuration upload, execution,
 * rollback, or verification probes.
 */
export type LifecycleStageId =
  | "requirements"
  | "site_scope"
  | "discovery"
  | "design"
  | "bom"
  | "capability"
  | "configuration_artifacts"
  | "virtual_validation"
  | "approval_readiness"
  | "post_change_verification";

export type LifecycleStageStatus = "ready" | "blocked" | "pending" | "not_applicable";

export type LifecycleStage = {
  id: LifecycleStageId;
  status: LifecycleStageStatus;
  blocker: string | null;
  evidenceSummary: string;
};

export type EndToEndLifecycleInput = {
  requirementsComplete: boolean;
  sectorReviewCurrent: boolean;
  registeredSiteCount: number;
  discoveryStates: Array<"queued" | "running" | "completed" | "partial" | "failed" | "blocked">;
  designRecorded: boolean;
  bomItemCount: number;
  observedDeviceCount: number;
  capabilityVerifiedDeviceCount: number;
  configArtifactCount: number;
  virtualValidationStates: Array<"not_tested" | "test_queued" | "test_passed" | "test_failed" | "test_inconclusive" | "not_supported_for_virtual_test">;
  approvalReadiness: Array<{ status: "ready_for_human_approval" | "blocked"; blockers: string[] }>;
  postChangeVerification: Array<{ state: "passed" | "failed" | "warning" | "not_verifiable"; rollbackReviewRequired: boolean }>;
};

function stage(id: LifecycleStageId, status: LifecycleStageStatus, evidenceSummary: string, blocker: string | null = null): LifecycleStage {
  return { id, status, blocker, evidenceSummary };
}

/**
 * Returns a deterministic, evidence-first handoff contract for all lifecycle
 * stages. A later stage may be pending, but cannot be presented as ready when
 * an earlier prerequisite remains blocked.
 */
export function assessEndToEndLifecycle(input: EndToEndLifecycleInput) {
  const stages: LifecycleStage[] = [];
  const requirementsBlocked = !input.requirementsComplete || !input.sectorReviewCurrent;
  stages.push(requirementsBlocked
    ? stage("requirements", "blocked", "Requirements and sector-review evidence were assessed.", !input.requirementsComplete ? "Requirements are incomplete." : "Sector review is stale or missing.")
    : stage("requirements", "ready", "Requirements and sector-review evidence are current."));

  stages.push(input.registeredSiteCount > 0
    ? stage("site_scope", "ready", `${input.registeredSiteCount} authorized site scope record(s) exist.`)
    : stage("site_scope", "blocked", "No authorized site scope record exists.", "Human-approved site scope is required before discovery."));

  const discoveryBlocked = input.discoveryStates.some(value => value === "failed" || value === "blocked" || value === "partial") || input.discoveryStates.length === 0;
  const discoveryComplete = input.discoveryStates.length > 0 && input.discoveryStates.every(value => value === "completed");
  stages.push(discoveryComplete
    ? stage("discovery", "ready", "All recorded discovery runs completed within their authorized scope.")
    : discoveryBlocked
      ? stage("discovery", "blocked", "Discovery evidence includes absent, partial, failed, or blocked collection.", "Resolve recorded discovery outcomes before downstream evidence is treated as ready.")
      : stage("discovery", "pending", "Authorized discovery collection is still queued or running."));

  stages.push(input.designRecorded
    ? stage("design", "ready", "A project design record is available for review.")
    : stage("design", "blocked", "No project design record is available.", "Record human-reviewable design decisions before artifact preparation."));
  stages.push(input.bomItemCount > 0
    ? stage("bom", "ready", `${input.bomItemCount} BOM item(s) are recorded.`)
    : stage("bom", "pending", "No BOM item is recorded; this may remain pending until equipment selection is in scope."));

  const capabilityBlocked = input.observedDeviceCount === 0 || input.capabilityVerifiedDeviceCount < input.observedDeviceCount;
  stages.push(capabilityBlocked
    ? stage("capability", "blocked", `${input.capabilityVerifiedDeviceCount} of ${input.observedDeviceCount} observed device(s) have verified capability evidence.`, "Every targeted observed device requires capability, license, and configuration-path evidence.")
    : stage("capability", "ready", `${input.capabilityVerifiedDeviceCount} observed device(s) have verified capability evidence.`));
  stages.push(input.configArtifactCount > 0
    ? stage("configuration_artifacts", "ready", `${input.configArtifactCount} capability-gated configuration artifact(s) are recorded.`)
    : stage("configuration_artifacts", "pending", "No configuration artifact is recorded."));

  const virtualBlocked = input.virtualValidationStates.some(value => value !== "test_passed") || input.virtualValidationStates.length === 0;
  stages.push(virtualBlocked
    ? stage("virtual_validation", "blocked", "Virtual-validation evidence is absent, pending, failed, inconclusive, unsupported, or not scope-ready.", "A current, scope-matched passed virtual test is required for every requested change plan.")
    : stage("virtual_validation", "ready", "Recorded virtual validation passed for every assessed change plan."));

  const approvalBlocked = input.approvalReadiness.some(value => value.status === "blocked") || input.approvalReadiness.length === 0;
  stages.push(approvalBlocked
    ? stage("approval_readiness", "blocked", "Approval-readiness assessment contains a blocker or no assessed change plan.", input.approvalReadiness.flatMap(value => value.blockers).at(0) || "A change-plan readiness assessment is required.")
    : stage("approval_readiness", "ready", "Change plans are ready to be presented for named human approval."));

  const verificationRequiresReview = input.postChangeVerification.some(value => value.rollbackReviewRequired || value.state === "failed" || value.state === "not_verifiable");
  stages.push(verificationRequiresReview
    ? stage("post_change_verification", "blocked", "Observed verification requires human rollback review.", "No automated rollback is available; a human must review the observed failed or unverifiable outcome.")
    : input.postChangeVerification.length
      ? stage("post_change_verification", "ready", "Observed post-change verification records do not require rollback review.")
      : stage("post_change_verification", "not_applicable", "Post-change verification starts only after an externally executed, human-approved change."));

  return {
    status: stages.some(value => value.status === "blocked") ? "blocked" as const : stages.some(value => value.status === "pending") ? "pending" as const : "ready_for_human_review" as const,
    stages,
    productionExecutionAllowed: false as const,
  };
}
