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

const { recordBenchmarkScenario } = await import("./autonet");

const actor = { id: 31, name: "Benchmark reviewer", email: "benchmark@example.test" };
const ownedProject = () => ({ id: 6, ownerId: actor.id });

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("benchmark scenario persistence", () => {
  it("records the human-supplied acceptance boundary without creating a universal claim", async () => {
    const reviewedAt = new Date();
    const stored = {
      id: 1,
      projectId: 6,
      scenarioId: "lab-scenario-001",
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
      acceptanceCriteriaReference: "criteria-reference",
      evidenceReference: "lab-evidence",
      reviewedAt,
      createdAt: reviewedAt,
      updatedAt: reviewedAt,
    };
    selectResults.push([ownedProject()], [ownedProject()], [stored]);

    const result = await recordBenchmarkScenario(6, {
      scenarioId: stored.scenarioId,
      vendorFamily: stored.vendorFamily,
      platform: stored.platform,
      model: stored.model,
      softwareVersion: stored.softwareVersion,
      licenseEvidenceReference: stored.licenseEvidenceReference,
      configurationPathReference: stored.configurationPathReference,
      sectorProfile: stored.sectorProfile,
      measuredRuns: stored.measuredRuns,
      acceptedRuns: stored.acceptedRuns,
      rejectedRuns: stored.rejectedRuns,
      minimumAcceptanceRatePercent: stored.minimumAcceptanceRatePercent,
      acceptanceCriteriaReference: stored.acceptanceCriteriaReference,
      evidenceReference: stored.evidenceReference,
      reviewedAt,
    }, actor);

    expect(result).toEqual([stored]);
    expect(insertCalls.find(value => typeof value === "object" && value !== null && "scenarioId" in value)).toMatchObject({ projectId: 6, scenarioId: "lab-scenario-001", minimumAcceptanceRatePercent: 80 });
  });
});
