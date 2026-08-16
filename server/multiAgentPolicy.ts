/** Pure status policy for the engineer-supervised multi-agent workflow. */

export type AgentWorkflowState = "blocked" | "awaiting_evidence" | "ready" | "completed" | "human_decision_required";

export type DiscoverySignal = {
  state: "queued" | "running" | "completed" | "partial" | "failed" | "blocked";
  ambiguousCount: number;
  unsupportedCount: number;
};

export type DeviceSignal = {
  factState: "unobserved" | "observed" | "ambiguous" | "unreachable" | "unsupported";
  capabilityVerified: boolean;
};

export type ApprovalReadinessSignal = {
  status: "blocked" | "ready_for_human_approval";
  blockers: readonly string[];
};

export type MultiAgentWorkflowInput = {
  registeredSiteCount: number;
  discoveryRuns: readonly DiscoverySignal[];
  devices: readonly DeviceSignal[];
  approvalReadiness: readonly ApprovalReadinessSignal[];
};

export type MultiAgentWorkflowStatus = {
  stages: ReadonlyArray<{
    role: "authorized_discovery" | "evidence_review" | "design_preparation" | "capability_assessment" | "virtual_validation" | "safety_review" | "release_coordination";
    state: AgentWorkflowState;
    detail: string;
  }>;
  humanGoNoGo: {
    state: "human_decision_required";
    detail: string;
  };
  productionExecution: {
    state: "blocked";
    detail: string;
  };
};

type AgentStageStatus = {
  state: AgentWorkflowState;
  detail: string;
};

function discoveryStatus(input: MultiAgentWorkflowInput): AgentStageStatus {
  if (input.registeredSiteCount === 0) {
    return { state: "blocked", detail: "Register a human-approved site scope before discovery can be assigned." };
  }
  if (input.discoveryRuns.length === 0) {
    return { state: "ready", detail: "A site scope is registered; an authorized read-only discovery run may be queued." };
  }
  const latestRun = input.discoveryRuns[0];
  if (latestRun.state === "completed" && latestRun.ambiguousCount === 0 && latestRun.unsupportedCount === 0) {
    return { state: "completed", detail: "The latest run completed without recorded ambiguous or unsupported targets." };
  }
  if (["partial", "failed", "blocked"].includes(latestRun.state) || latestRun.ambiguousCount > 0 || latestRun.unsupportedCount > 0) {
    return { state: "blocked", detail: "Discovery has unresolved, unsupported, failed, or partial evidence that requires engineer review." };
  }
  return { state: "awaiting_evidence", detail: "Read-only discovery is queued or running; no downstream agent may treat it as verified evidence." };
}

function deviceEvidenceStatus(input: MultiAgentWorkflowInput, discovery: AgentStageStatus): AgentStageStatus {
  if (discovery.state === "blocked") {
    return { state: "blocked", detail: "Evidence review is blocked until discovery ambiguity and unsupported paths are resolved or explicitly refused." };
  }
  if (discovery.state !== "completed") {
    return { state: "awaiting_evidence", detail: "Evidence review waits for a completed discovery run with recorded outcomes." };
  }
  if (input.devices.length === 0) {
    return { state: "awaiting_evidence", detail: "Record observed device facts before design or capability assessment." };
  }
  if (input.devices.some(device => device.factState !== "observed")) {
    return { state: "blocked", detail: "At least one device lacks an observed fact state; no fact may be inferred." };
  }
  return { state: "ready", detail: "Observed device facts are available for the evidence reviewer and design specialist." };
}

function capabilityStatus(input: MultiAgentWorkflowInput, evidence: AgentStageStatus): AgentStageStatus {
  if (evidence.state === "blocked") {
    return { state: "blocked", detail: "Capability assessment is blocked until every affected device has observed facts." };
  }
  if (evidence.state !== "ready") {
    return { state: "awaiting_evidence", detail: "Capability assessment requires observed device facts and exact version/license evidence." };
  }
  if (input.devices.some(device => !device.capabilityVerified)) {
    return { state: "blocked", detail: "At least one observed device has no exact capability verification; configuration must remain blocked." };
  }
  return { state: "ready", detail: "Observed devices are capability-verified; a separately reviewed artifact and virtual test remain required." };
}

function safetyReviewStatus(input: MultiAgentWorkflowInput, capability: AgentStageStatus): AgentStageStatus {
  if (capability.state === "blocked") {
    return { state: "blocked", detail: "Safety review cannot proceed while discovery, device evidence, or capability assessment remains blocked." };
  }
  if (input.approvalReadiness.length === 0) {
    return { state: "awaiting_evidence", detail: "Safety review waits for a hash-bound change plan and its current validation, backup, maintenance, and authority evidence." };
  }
  const blockedReadiness = input.approvalReadiness.find(readiness => readiness.status === "blocked");
  if (blockedReadiness) {
    return {
      state: "blocked",
      detail: `A change-plan release gate is blocked: ${blockedReadiness.blockers.join(" ") || "required evidence is incomplete."}`,
    };
  }
  return { state: "ready", detail: "The recorded change-plan evidence is ready for a named human Go/No-Go decision; agents cannot approve it." };
}

export function assessMultiAgentWorkflow(input: MultiAgentWorkflowInput): MultiAgentWorkflowStatus {
  /** Describe preparation readiness without creating release or production authority. */

  const discovery = discoveryStatus(input);
  const evidence = deviceEvidenceStatus(input, discovery);
  const capability = capabilityStatus(input, evidence);
  const safetyReview = safetyReviewStatus(input, capability);
  return {
    stages: [
      { role: "authorized_discovery", ...discovery },
      { role: "evidence_review", ...evidence },
      {
        role: "design_preparation",
        state: evidence.state === "ready" ? "ready" : evidence.state,
        detail: evidence.state === "ready"
          ? "Design preparation may use only the reviewed observed facts and approved requirements."
          : "Design preparation remains bounded by the discovery and evidence-review result.",
      },
      { role: "capability_assessment", ...capability },
      {
        role: "virtual_validation",
        state: capability.state === "ready" ? "awaiting_evidence" : capability.state,
        detail: capability.state === "ready"
          ? "A hash-bound artifact, target facts, scope, supported validation path, and recorded test result are still required."
          : "Virtual validation cannot begin on an unresolved capability path.",
      },
      {
        role: "safety_review",
        ...safetyReview,
      },
      {
        role: "release_coordination",
        state: "human_decision_required",
        detail: "A named human authority must make the Go/No-Go decision after all controls are proven.",
      },
    ],
    humanGoNoGo: {
      state: "human_decision_required",
      detail: "Specialized agents may prepare evidence and a review pack, but cannot approve, waive blockers, or issue Go.",
    },
    productionExecution: {
      state: "blocked",
      detail: "The coordinated workflow does not expose automatic production configuration upload or execution.",
    },
  };
}
