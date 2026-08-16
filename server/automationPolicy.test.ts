import { describe, expect, it } from "vitest";
import { assessRecommendation, assessRestrictedClaim, evaluateApprovalReadiness, evaluateChangeRelease, resolveClaimStatus } from "./automationPolicy";

describe("automation policy", () => {
  const validInput = {
    requirementsComplete: true,
    targetFactsCurrent: true,
    deviceCapabilityVerified: true,
    virtualValidation: "test_passed" as const,
    virtualTestScopeMatches: true,
    virtualTestCurrent: true,
    backupVerified: true,
    maintenanceWindowValid: true,
    humanApprovalGranted: true,
  };

  it("requires every independent safety control before execution eligibility", () => {
    expect(evaluateChangeRelease(validInput)).toEqual({ status: "eligible_for_execution", blockers: [] });
    expect(evaluateChangeRelease({ ...validInput, humanApprovalGranted: false })).toMatchObject({
      status: "blocked",
      blockers: ["A named human approval is required."],
    });
  });

  it("does not allow a successful virtual test to bypass stale facts or backup controls", () => {
    const decision = evaluateChangeRelease({ ...validInput, targetFactsCurrent: false, backupVerified: false });
    expect(decision.status).toBe("blocked");
    expect(decision.blockers).toContain("Target device facts are missing or stale.");
    expect(decision.blockers).toContain("A current backup is not verified.");
  });

  it("can request human approval without treating that request as a granted approval", () => {
    const { humanApprovalGranted: _, ...approvalInput } = validInput;
    expect(evaluateApprovalReadiness(approvalInput)).toEqual({ status: "ready_for_human_approval", blockers: [] });
  });

  it("does not turn missing evidence into a positive claim", () => {
    expect(resolveClaimStatus(false)).toBe("insufficient_evidence");
    expect(resolveClaimStatus(true)).toBe("verified");
  });

  it("blocks every restricted claim class without scoped and reviewed evidence", () => {
    const incomplete = assessRestrictedClaim({
      claimClass: "production_safe",
      scopeDescription: "",
      authorityReference: "",
      measuredEvidenceReference: "",
      reviewedAt: null,
    });
    expect(incomplete.status).toBe("blocked");
    expect(incomplete.missing).toHaveLength(4);

    expect(assessRestrictedClaim({
      claimClass: "compatibility",
      scopeDescription: "Cisco IOS XE 17.13 path under documented lab scope",
      authorityReference: "vendor-guide-reference",
      measuredEvidenceReference: "lab-run-2026-08-15",
      reviewedAt: new Date("2026-08-15T00:00:00.000Z"),
    })).toEqual({ status: "publishable", missing: [] });
  });

  it("abstains rather than guessing when a recommendation lacks facts, scope, or a named authority", () => {
    const result = assessRecommendation({
      sourceFacts: [],
      uncertainty: ["Model release is unknown"],
      rationale: "",
      alternatives: [],
      affectedDevices: [],
      unresolvedItems: ["Model release is unknown"],
      requiredAuthority: null,
    });
    expect(result.status).toBe("abstain");
    expect(result.reasons).toContain("No observed source facts are attached.");
    expect(result.reasons).toContain("No required human authority is assigned.");
  });

  it("allows an evidenced recommendation to proceed only to human review", () => {
    const evidence = {
      sourceFacts: ["Observed platform and version"],
      uncertainty: ["No unresolved uncertainty remains within the stated scope."],
      rationale: "Capability evidence matches the requested path.",
      alternatives: ["Do not change the device"],
      affectedDevices: ["device-record-01"],
      unresolvedItems: [],
      requiredAuthority: "reviewer",
    } as const;
    expect(assessRecommendation(evidence)).toEqual({ status: "ready_for_human_review", reasons: [], evidence });
  });
});
