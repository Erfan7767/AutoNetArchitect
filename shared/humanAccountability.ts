export type HumanAccountabilityRole = "reviewer" | "approver" | "executor" | "emergency_authorizer";
export type HumanAccountabilityState = "required" | "recorded" | "external_only" | "external_policy_only";

export type HumanAccountabilityItem = {
  role: HumanAccountabilityRole;
  label: string;
  state: HumanAccountabilityState;
  detail: string;
};

/**
 * Describes distinct responsibilities without inferring an assigned individual
 * or granting any authority that is not explicitly persisted elsewhere.
 */
export function getHumanAccountability(approvalState: string): HumanAccountabilityItem[] {
  return [
    {
      role: "reviewer",
      label: "Technical review",
      state: "required",
      detail: "A qualified reviewer must assess source facts, uncertainty, rationale, alternatives, affected scope, and unresolved items.",
    },
    {
      role: "approver",
      label: "Change approval",
      state: approvalState === "approved" ? "recorded" : "required",
      detail: approvalState === "approved"
        ? "A project approval state is recorded. Each change plan still requires its own current evidence and approval gates."
        : "A named approver may decide only after all applicable evidence, validation, backup, maintenance, and scope gates are ready.",
    },
    {
      role: "executor",
      label: "Execution authority",
      state: "external_only",
      detail: "An authorized human executor must use an approved external change process. This control plane cannot upload configuration or execute a production change.",
    },
    {
      role: "emergency_authorizer",
      label: "Emergency exception",
      state: "external_policy_only",
      detail: "Emergency authority must be declared and audited under an external emergency policy. It cannot waive evidence gates or enable automatic execution here.",
    },
  ];
}
