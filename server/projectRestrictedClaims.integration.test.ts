import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TrpcContext } from "./_core/context";

const selectResults: unknown[][] = [];
const insertCalls: unknown[] = [];

const queryBuilder = () => {
  const builder: Record<string, (...args: unknown[]) => unknown> = {};
  builder.from = () => builder;
  builder.where = () => builder;
  builder.limit = async () => selectResults.shift() || [];
  builder.orderBy = async () => selectResults.shift() || [];
  return builder;
};

const fakeDb = {
  select: vi.fn(() => queryBuilder()),
  insert: vi.fn(() => ({ values: (value: unknown) => { insertCalls.push(value); return Promise.resolve(); } })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { appRouter } = await import("./routers");

function context(): TrpcContext {
  return {
    user: { id: 27, openId: "claim-report-user", email: "claim-report@example.test", name: "Claim report user", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const ownedProject = () => ({ id: 4, ownerId: 27 });
const reviewableScenario = {
  scenarioId: "recorded-scenario",
  vendorFamily: "cisco" as const,
  platform: "ios_xe",
  model: "C9300-48P",
  softwareVersion: "17.9.4",
  licenseEvidenceReference: "license-reference",
  configurationPathReference: "configuration-path-reference",
  sectorProfile: "enterprise" as const,
  measuredRuns: 3,
  acceptedRuns: 2,
  rejectedRuns: 1,
  evidenceReference: "measured-evidence",
  reviewedAt: new Date(),
};

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("projects.restrictedClaims integration", () => {
  it("records a blocked assessment when required scope evidence is absent", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([ownedProject()], [ownedProject()], []);

    const result = await caller.projects.restrictedClaims.record({
      projectId: 4,
      claimClass: "production_safe",
      scopeDescription: "",
      authorityReference: "",
      measuredEvidenceReference: "",
      reviewedAt: null,
      benchmarkScenario: { ...reviewableScenario, measuredRuns: 0, acceptedRuns: 0, rejectedRuns: 0 },
    });

    expect(result.status).toBe("blocked");
    expect(result.missing.length).toBeGreaterThan(0);
    expect(insertCalls.find(value => typeof value === "object" && value !== null && "assessmentStatus" in value)).toMatchObject({ projectId: 4, claimClass: "production_safe", assessmentStatus: "blocked" });
  });

  it("blocks an otherwise scoped claim when no matching persisted measured scenario exists", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([ownedProject()], [], [ownedProject()], [ownedProject()], []);

    const result = await caller.projects.restrictedClaims.record({
      projectId: 4,
      claimClass: "compatibility",
      scopeDescription: "Exact Cisco laboratory path.",
      authorityReference: "Reviewed official reference.",
      measuredEvidenceReference: "Measured lab evidence.",
      reviewedAt: new Date(),
      benchmarkScenario: reviewableScenario,
    });

    expect(result.status).toBe("blocked");
    expect(result.missing).toContain("No matching persisted benchmark scenario meets its recorded acceptance criteria for this restricted claim scope.");
  });

  it("permits a scoped claim only when its matching persisted scenario meets acceptance criteria", async () => {
    const now = new Date();
    const storedScenario = { id: 4, projectId: 4, ...reviewableScenario, minimumAcceptanceRatePercent: 60, acceptanceCriteriaReference: "reviewed-criteria", createdAt: now, updatedAt: now };
    selectResults.push([ownedProject()], [storedScenario], [ownedProject()], [ownedProject()], []);
    const caller = appRouter.createCaller(context());

    const result = await caller.projects.restrictedClaims.record({
      projectId: 4,
      claimClass: "compatibility",
      scopeDescription: "Exact Cisco laboratory path.",
      authorityReference: "Reviewed official reference.",
      measuredEvidenceReference: "Measured lab evidence.",
      reviewedAt: now,
      benchmarkScenario: { ...reviewableScenario, minimumAcceptanceRatePercent: 60, acceptanceCriteriaReference: "reviewed-criteria" },
    });

    expect(result.status).toBe("publishable");
  });

  it.each([
    ["vendor", { vendorFamily: "huawei" as const }],
    ["model", { model: "C9200-48P" }],
    ["version", { softwareVersion: "17.12.1" }],
    ["sector", { sectorProfile: "industrial" as const }],
  ])("blocks a scoped claim when the persisted scenario has a mismatched %s", async (_dimension, override) => {
    const now = new Date();
    const storedScenario = { id: 5, projectId: 4, ...reviewableScenario, minimumAcceptanceRatePercent: 60, acceptanceCriteriaReference: "reviewed-criteria", ...override, createdAt: now, updatedAt: now };
    selectResults.push([ownedProject()], [storedScenario], [ownedProject()], [ownedProject()], []);
    const caller = appRouter.createCaller(context());

    const result = await caller.projects.restrictedClaims.record({
      projectId: 4,
      claimClass: "compatibility",
      scopeDescription: "Exact Cisco laboratory path.",
      authorityReference: "Reviewed official reference.",
      measuredEvidenceReference: "Measured lab evidence.",
      reviewedAt: now,
      benchmarkScenario: { ...reviewableScenario, minimumAcceptanceRatePercent: 60, acceptanceCriteriaReference: "reviewed-criteria" },
    });

    expect(result.status).toBe("blocked");
    expect(result.missing).toContain("No matching persisted benchmark scenario meets its recorded acceptance criteria for this restricted claim scope.");
  });

  it("returns project-scoped report entries and does not elevate absent classes", async () => {
    const caller = appRouter.createCaller(context());
    const now = new Date();
    selectResults.push([ownedProject()], [{
      id: 1, projectId: 4, claimClass: "compatibility", scopeDescription: "Exact laboratory scenario only.", authorityReference: "Official source.", measuredEvidenceReference: "Measured evidence.", reviewedAt: now, assessmentStatus: "publishable", createdAt: now, updatedAt: now,
    }]);

    const report = await caller.projects.restrictedClaims.report({ projectId: 4 });

    expect(report.find(entry => entry.claimClass === "compatibility")).toMatchObject({ status: "publishable" });
    expect(report.find(entry => entry.claimClass === "compliance")).toMatchObject({ status: "blocked" });
  });
});
