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
