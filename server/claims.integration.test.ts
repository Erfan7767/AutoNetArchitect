import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

function createContext(): TrpcContext {
  return {
    user: {
      id: 1,
      openId: "claim-test-user",
      email: "claim-test@example.com",
      name: "Claim Test User",
      loginMethod: "manus",
      role: "user",
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const benchmarkScenario = {
  scenarioId: "bank-cisco-iosxe-17-9-lab-001",
  vendorFamily: "cisco" as const,
  platform: "ios_xe",
  softwareVersion: "17.9.4",
  licenseEvidenceReference: "license-evidence-001",
  configurationPathReference: "candidate-commit-path-001",
  sectorProfile: "financial_service_branch" as const,
  measuredRuns: 3,
  acceptedRuns: 2,
  rejectedRuns: 1,
  evidenceReference: "lab-evidence-001",
  reviewedAt: new Date(),
};

describe("claims.assessPublication integration path", () => {
  it.each([
    ["missing authoritative reference", { authorityReference: "" }],
    ["missing measured evidence", { measuredEvidenceReference: "" }],
    ["missing review timestamp", { reviewedAt: null }],
  ])("blocks a restricted claim with %s", async (_label, overrides) => {
    const caller = appRouter.createCaller(createContext());
    const result = await caller.claims.assessPublication({
      claimClass: "production_safe",
      scopeDescription: "Cisco IOS XE laboratory scenario only.",
      authorityReference: "Vendor release note reference.",
      measuredEvidenceReference: "Pilot run P-001.",
      reviewedAt: new Date(),
      benchmarkScenario,
      ...overrides,
    });

    expect(result.status).toBe("blocked");
    expect(result.missing.length).toBeGreaterThan(0);
  });

  it("does not turn an evidence-complete assessment into a published claim", async () => {
    const caller = appRouter.createCaller(createContext());
    const result = await caller.claims.assessPublication({
      claimClass: "compatibility",
      scopeDescription: "A stated model/version/license/path combination only.",
      authorityReference: "Official vendor source reference.",
      measuredEvidenceReference: "Recorded laboratory evidence identifier.",
      reviewedAt: new Date(),
      benchmarkScenario,
    });

    expect(result).toEqual({ status: "publishable", missing: [] });
  });

  it("blocks an otherwise complete claim outside measured benchmark coverage", async () => {
    const caller = appRouter.createCaller(createContext());
    const result = await caller.claims.assessPublication({
      claimClass: "compatibility",
      scopeDescription: "A stated model/version/license/path combination only.",
      authorityReference: "Official vendor source reference.",
      measuredEvidenceReference: "Recorded laboratory evidence identifier.",
      reviewedAt: new Date(),
      benchmarkScenario: { ...benchmarkScenario, softwareVersion: "", measuredRuns: 0, acceptedRuns: 0, rejectedRuns: 0 },
    });

    expect(result.status).toBe("blocked");
    expect(result.missing).toContain("Exact platform and software version are required.");
  });
});

describe("recommendations.assess integration path", () => {
  it("abstains when evidence or human authority is missing", async () => {
    const caller = appRouter.createCaller(createContext());
    const result = await caller.recommendations.assess({
      sourceFacts: [],
      rationale: "",
      alternatives: [],
      affectedDevices: [],
      unresolvedItems: ["Exact platform/version evidence is not supplied."],
      requiredAuthority: null,
    });

    expect(result.status).toBe("abstain");
    expect(result.reasons).toContain("No observed source facts are attached.");
    expect(result.reasons).toContain("No required human authority is assigned.");
  });

  it("permits human review only when the evidence record is complete", async () => {
    const caller = appRouter.createCaller(createContext());
    const result = await caller.recommendations.assess({
      sourceFacts: ["Observed facts hash: abc123"],
      rationale: "The option matches the recorded design intent.",
      alternatives: ["Retain the current approved design."],
      affectedDevices: ["device-reference-01"],
      unresolvedItems: [],
      requiredAuthority: "reviewer",
    });

    expect(result).toEqual({ status: "ready_for_human_review", reasons: [] });
  });
});
