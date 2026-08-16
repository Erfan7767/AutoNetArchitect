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
    user: { id: 53, openId: "benchmark-user", email: "benchmark@example.test", name: "Benchmark reviewer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const ownedProject = () => ({ id: 8, ownerId: 53 });
const scenarioInput = {
  projectId: 8,
  scenarioId: "enterprise-cisco-lab-001",
  vendorFamily: "cisco" as const,
  platform: "ios_xe",
  model: "C9300-48P",
  softwareVersion: "17.9.4",
  licenseEvidenceReference: "license-evidence",
  configurationPathReference: "candidate-commit-path",
  sectorProfile: "enterprise" as const,
  measuredRuns: 5,
  acceptedRuns: 4,
  rejectedRuns: 1,
  minimumAcceptanceRatePercent: 80,
  acceptanceCriteriaReference: "approved-acceptance-criteria",
  evidenceReference: "measured-lab-evidence",
  reviewedAt: new Date(),
};

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("projects.benchmarks integration", () => {
  it("records an owned measured scenario and returns measured coverage only for its declared scope", async () => {
    const now = new Date();
    const stored = { id: 1, ...scenarioInput, reviewedAt: now, createdAt: now, updatedAt: now };
    selectResults.push([ownedProject()], [ownedProject()], [stored]);
    const caller = appRouter.createCaller(context());

    const result = await caller.projects.benchmarks.record(scenarioInput);

    expect(result.coverage).toEqual({ status: "measured_coverage", blockers: [] });
    expect(result.scenarios).toEqual([stored]);
    expect(insertCalls.find(value => typeof value === "object" && value !== null && "scenarioId" in value)).toMatchObject({ projectId: 8, scenarioId: "enterprise-cisco-lab-001", minimumAcceptanceRatePercent: 80 });
  });

  it("retains a failed acceptance criterion as blocked coverage rather than elevating it", async () => {
    const now = new Date();
    const stored = { id: 2, ...scenarioInput, minimumAcceptanceRatePercent: 90, reviewedAt: now, createdAt: now, updatedAt: now };
    selectResults.push([ownedProject()], [ownedProject()], [stored]);
    const caller = appRouter.createCaller(context());

    const result = await caller.projects.benchmarks.record({ ...scenarioInput, minimumAcceptanceRatePercent: 90 });

    expect(result.coverage.status).toBe("outside_measured_coverage");
    expect(result.coverage.blockers).toContain("Measured acceptance does not meet the recorded minimum acceptance rate.");
  });

  it("rejects an epoch review timestamp instead of accepting synthetic review metadata", async () => {
    const caller = appRouter.createCaller(context());
    await expect(caller.projects.benchmarks.record({ ...scenarioInput, reviewedAt: new Date(0) })).rejects.toThrow("A human review date is required.");
  });

  it("returns no benchmark list for a project not owned by the caller", async () => {
    selectResults.push([]);
    const caller = appRouter.createCaller(context());
    await expect(caller.projects.benchmarks.list({ projectId: 999 })).rejects.toThrow();
  });
});
