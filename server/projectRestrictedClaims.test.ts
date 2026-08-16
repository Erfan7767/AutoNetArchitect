import { beforeEach, describe, expect, it, vi } from "vitest";

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

const { recordProjectRestrictedClaim } = await import("./autonet");
const { buildRestrictedClaimReport } = await import("./claimReportPolicy");

const actor = { id: 19, name: "Claim reviewer", email: "reviewer@example.test" };
const ownedProject = () => ({ id: 8, ownerId: actor.id });

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("project restricted claim records", () => {
  it("persists a scoped claim assessment and keeps absent classes blocked in the report", async () => {
    const reviewedAt = new Date();
    const storedRecord = {
      id: 1,
      projectId: 8,
      claimClass: "compatibility" as const,
      scopeDescription: "Exact reviewed laboratory scenario only.",
      authorityReference: "Official vendor source.",
      measuredEvidenceReference: "Measured laboratory evidence.",
      reviewedAt,
      assessmentStatus: "publishable" as const,
      createdAt: reviewedAt,
      updatedAt: reviewedAt,
    };
    selectResults.push([ownedProject()], [ownedProject()], [storedRecord]);

    const records = await recordProjectRestrictedClaim(8, {
      claimClass: "compatibility",
      scopeDescription: storedRecord.scopeDescription,
      authorityReference: storedRecord.authorityReference,
      measuredEvidenceReference: storedRecord.measuredEvidenceReference,
      reviewedAt,
      assessmentStatus: "publishable",
    }, actor);

    expect(records).toEqual([storedRecord]);
    expect(insertCalls.find(value => typeof value === "object" && value !== null && "claimClass" in value)).toMatchObject({ projectId: 8, claimClass: "compatibility", assessmentStatus: "publishable" });
    const report = buildRestrictedClaimReport(records || []);
    expect(report.find(item => item.claimClass === "compatibility")?.status).toBe("publishable");
    expect(report.find(item => item.claimClass === "production_safe")?.status).toBe("blocked");
  });

  it("retains a blocked assessment as blocked even when its base fields are complete", () => {
    const report = buildRestrictedClaimReport([{
      claimClass: "production_safe",
      scopeDescription: "Narrow scenario only.",
      authorityReference: "Official source.",
      measuredEvidenceReference: "Measured evidence.",
      reviewedAt: new Date(),
      assessmentStatus: "blocked",
    }]);

    expect(report.find(item => item.claimClass === "production_safe")).toMatchObject({ status: "blocked" });
    expect(report.find(item => item.claimClass === "production_safe")?.blockers[0]).toContain("recorded scoped claim assessment remains blocked");
  });
});
