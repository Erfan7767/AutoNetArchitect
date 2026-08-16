import { describe, expect, it } from "vitest";
import { assessMultiAgentWorkflow } from "./multiAgentPolicy";

describe("multi-agent workflow policy", () => {
  it("blocks discovery when no human-approved site scope is registered", () => {
    const status = assessMultiAgentWorkflow({ registeredSiteCount: 0, discoveryRuns: [], devices: [], approvalReadiness: [] });

    expect(status.stages[0]).toMatchObject({ role: "authorized_discovery", state: "blocked" });
    expect(status.productionExecution.state).toBe("blocked");
  });

  it("blocks downstream coordination when discovery contains an ambiguous target", () => {
    const status = assessMultiAgentWorkflow({
      registeredSiteCount: 1,
      discoveryRuns: [{ state: "completed", ambiguousCount: 1, unsupportedCount: 0 }],
      devices: [],
      approvalReadiness: [],
    });

    expect(status.stages[0].state).toBe("blocked");
    expect(status.stages[1].state).toBe("blocked");
    expect(status.stages[2].state).toBe("blocked");
  });

  it("still requires virtual evidence and a human decision for fully observed verified devices", () => {
    const status = assessMultiAgentWorkflow({
      registeredSiteCount: 1,
      discoveryRuns: [{ state: "completed", ambiguousCount: 0, unsupportedCount: 0 }],
      devices: [{ factState: "observed", capabilityVerified: true }],
      approvalReadiness: [],
    });

    expect(status.stages[0].state).toBe("completed");
    expect(status.stages[3].state).toBe("ready");
    expect(status.stages[4].state).toBe("awaiting_evidence");
    expect(status.humanGoNoGo.state).toBe("human_decision_required");
    expect(status.productionExecution.state).toBe("blocked");
  });

  it("keeps failed, stale, unsupported, and unapproved paths out of production through coordination", () => {
    const status = assessMultiAgentWorkflow({
      registeredSiteCount: 1,
      discoveryRuns: [{ state: "completed", ambiguousCount: 0, unsupportedCount: 1 }],
      devices: [{ factState: "observed", capabilityVerified: true }],
      approvalReadiness: [{
        status: "blocked",
        blockers: [
          "Virtual validation failed.",
          "Virtual validation evidence is stale.",
          "A named human approval is still required.",
        ],
      }],
    });

    expect(status.stages[0].state).toBe("blocked");
    expect(status.stages[5].state).toBe("blocked");
    expect(status.humanGoNoGo.state).toBe("human_decision_required");
    expect(status.productionExecution.state).toBe("blocked");
  });
});
