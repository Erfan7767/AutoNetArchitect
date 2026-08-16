import { describe, expect, it } from "vitest";
import { assessEndToEndLifecycle } from "./lifecycleContract";

const completeInput = {
  requirementsComplete: true,
  sectorReviewCurrent: true,
  registeredSiteCount: 1,
  discoveryStates: ["completed"] as const,
  designRecorded: true,
  bomItemCount: 1,
  observedDeviceCount: 1,
  capabilityVerifiedDeviceCount: 1,
  configArtifactCount: 1,
  virtualValidationStates: ["test_passed"] as const,
  approvalReadiness: [{ status: "ready_for_human_approval" as const, blockers: [] }],
  postChangeVerification: [],
};

describe("assessEndToEndLifecycle", () => {
  it("returns a traceable pre-execution chain without granting production authority", () => {
    const result = assessEndToEndLifecycle(completeInput);

    expect(result.status).toBe("ready_for_human_review");
    expect(result.stages.map(value => value.id)).toEqual([
      "requirements", "site_scope", "discovery", "design", "bom", "capability", "configuration_artifacts", "virtual_validation", "approval_readiness", "post_change_verification",
    ]);
    expect(result.productionExecutionAllowed).toBe(false);
  });

  it("preserves exact blockers from missing capability and failed virtual validation", () => {
    const result = assessEndToEndLifecycle({
      ...completeInput,
      capabilityVerifiedDeviceCount: 0,
      virtualValidationStates: ["test_failed"],
      approvalReadiness: [{ status: "blocked", blockers: ["Virtual validation state is test_failed."] }],
    });

    expect(result.status).toBe("blocked");
    expect(result.stages.find(value => value.id === "capability")?.blocker).toContain("Every targeted observed device");
    expect(result.stages.find(value => value.id === "approval_readiness")?.blocker).toBe("Virtual validation state is test_failed.");
    expect(result.productionExecutionAllowed).toBe(false);
  });

  it("blocks the requirements stage when sector review is stale despite a saved project timestamp", () => {
    const result = assessEndToEndLifecycle({
      ...completeInput,
      sectorReviewCurrent: false,
    });

    expect(result.status).toBe("blocked");
    expect(result.stages.find(value => value.id === "requirements")).toMatchObject({
      status: "blocked",
      blocker: "Sector review is stale or missing.",
    });
  });

  it("converts a failed observed outcome into a rollback-review block without rollback authority", () => {
    const result = assessEndToEndLifecycle({
      ...completeInput,
      postChangeVerification: [{ state: "failed", rollbackReviewRequired: true }],
    });

    expect(result.status).toBe("blocked");
    expect(result.stages.find(value => value.id === "post_change_verification")?.blocker).toContain("No automated rollback");
    expect(result.productionExecutionAllowed).toBe(false);
  });
});
