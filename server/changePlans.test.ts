import { beforeEach, describe, expect, it, vi } from "vitest";

const selectResults: unknown[][] = [];
const insertCalls: unknown[] = [];

const queryBuilder = () => {
  const builder: Record<string, (...args: unknown[]) => unknown> = {};
  builder.from = () => builder;
  builder.innerJoin = () => builder;
  builder.where = () => builder;
  builder.limit = async () => selectResults.shift() || [];
  builder.orderBy = async () => selectResults.shift() || [];
  return builder;
};

const fakeDb = {
  select: vi.fn(() => queryBuilder()),
  insert: vi.fn(() => ({
    values: (value: unknown) => {
      insertCalls.push(value);
      const promise = Promise.resolve();
      Object.assign(promise, { $returningId: async () => [{ id: 55 }] });
      return promise;
    },
  })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { createChangePlan } = await import("./autonet");

const actor = { id: 11, name: "Reviewer", email: "reviewer@example.test" };
const enterpriseInputs = [
  "Business-service priorities and outage impact",
  "Site and management-network boundaries",
  "Identity, segmentation, and internet-edge policy",
  "Supported hardware, software, license, and support evidence",
  "Change authority and maintenance policy",
];

function projectWithSector(sectorInputsUpdatedAt: Date | null) {
  return {
    id: 1,
    ownerId: actor.id,
    sectorProfile: "enterprise",
    sectorInputs: JSON.stringify(enterpriseInputs),
    sectorInputsUpdatedAt,
  };
}

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("change-plan sector review gate", () => {
  it("rejects a stale sector review before reading device facts", async () => {
    const stale = new Date(Date.now() - 91 * 24 * 60 * 60 * 1000);
    selectResults.push([projectWithSector(stale)]);

    await expect(createChangePlan(1, {
      deviceId: 10,
      name: "Branch edge change",
      artifactHash: "artifact-hash",
      scopeHash: "scope-hash",
    }, actor)).rejects.toThrow("Sector profile review is stale or missing");
    expect(insertCalls).toHaveLength(0);
    expect(selectResults).toHaveLength(0);
  });

  it("rejects an incomplete sector profile before reading device facts", async () => {
    const incompleteProject = projectWithSector(new Date());
    incompleteProject.sectorInputs = JSON.stringify([enterpriseInputs[0]]);
    selectResults.push([incompleteProject]);

    await expect(createChangePlan(1, {
      deviceId: 10,
      name: "Incomplete branch change",
      artifactHash: "artifact-hash",
      scopeHash: "scope-hash",
    }, actor)).rejects.toThrow("Sector profile is incomplete");
    expect(insertCalls).toHaveLength(0);
  });

  it("stores a complete sector snapshot and deterministic input hash", async () => {
    const reviewedAt = new Date();
    const project = projectWithSector(reviewedAt);
    const device = { device: { id: 10, factState: "observed", factsHash: "facts-hash", capabilityVerified: true }, project };
    selectResults.push([project], [device], [project], []);

    await createChangePlan(1, {
      deviceId: 10,
      name: "Branch edge change",
      artifactHash: "artifact-hash",
      scopeHash: "scope-hash",
    }, actor);

    const planInsert = insertCalls.find(value => typeof value === "object" && value !== null && "sectorProfileSnapshot" in value) as Record<string, unknown> | undefined;
    expect(planInsert).toBeDefined();
    expect(planInsert?.sectorReviewState).toBe("current");
    expect(planInsert?.sectorInputsHash).toMatch(/^[a-f0-9]{64}$/);
    expect(JSON.parse(String(planInsert?.sectorProfileSnapshot))).toMatchObject({ profileId: "enterprise", completenessPercent: 100 });
    expect(planInsert?.sectorReviewedAt).toEqual(reviewedAt);
  });
});
