import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TrpcContext } from "./_core/context";

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
      Object.assign(promise, { $returningId: async () => [{ id: 77 }] });
      return promise;
    },
  })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { appRouter } = await import("./routers");

const actor = {
  id: 11,
  openId: "reviewer-open-id",
  email: "reviewer@example.test",
  name: "Reviewer",
  loginMethod: "test",
  role: "user" as const,
  createdAt: new Date(),
  updatedAt: new Date(),
  lastSignedIn: new Date(),
};

const enterpriseInputs = [
  "Business-service priorities and outage impact",
  "Site and management-network boundaries",
  "Identity, segmentation, and internet-edge policy",
  "Supported hardware, software, license, and support evidence",
  "Change authority and maintenance policy",
];

const context: TrpcContext = {
  user: actor,
  req: { protocol: "https", headers: {} } as TrpcContext["req"],
  res: {} as TrpcContext["res"],
};

function project(sectorProfile: string, inputs: string[], reviewedAt: Date | null) {
  return {
    id: 1,
    ownerId: actor.id,
    sectorProfile,
    sectorInputs: JSON.stringify(inputs),
    sectorInputsUpdatedAt: reviewedAt,
  };
}

const input = {
  projectId: 1,
  deviceId: 10,
  name: "Branch edge change",
  artifactHash: "artifact-hash",
  scopeHash: "scope-hash",
};

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("projects.changePlans.create real integration path", () => {
  it.each([
    ["unselected", project("unselected", [], new Date())],
    ["incomplete", project("enterprise", [enterpriseInputs[0]], new Date())],
    ["stale", project("enterprise", enterpriseInputs, new Date(Date.now() - 91 * 24 * 60 * 60 * 1000))],
  ])("rejects %s sector state before persistence", async (_label, projectRecord) => {
    selectResults.push([projectRecord]);
    const caller = appRouter.createCaller(context);

    await expect(caller.projects.changePlans.create(input)).rejects.toThrow();
    expect(insertCalls).toHaveLength(0);
  });

  it("persists and returns sector snapshot fields for a complete current state", async () => {
    const reviewedAt = new Date();
    const projectRecord = project("enterprise", enterpriseInputs, reviewedAt);
    const deviceRecord = { device: { id: 10, factState: "observed", factsHash: "facts-hash" }, project: projectRecord };
    const persistedPlan = {
      ...input,
      id: 77,
      targetFactsHash: "facts-hash",
      virtualValidationState: "not_tested",
      releaseState: "draft",
      sectorProfileSnapshot: JSON.stringify({ profileId: "enterprise", completenessPercent: 100 }),
      sectorInputsHash: "b".repeat(64),
      sectorReviewState: "current",
      sectorReviewedAt: reviewedAt,
    };
    selectResults.push([projectRecord], [deviceRecord], [projectRecord], [persistedPlan]);
    const caller = appRouter.createCaller(context);

    const result = await caller.projects.changePlans.create(input);

    const planInsert = insertCalls.find(value => typeof value === "object" && value !== null && "sectorProfileSnapshot" in value) as Record<string, unknown> | undefined;
    expect(planInsert?.sectorReviewState).toBe("current");
    expect(planInsert?.sectorInputsHash).toMatch(/^[a-f0-9]{64}$/);
    expect(result[0]?.sectorReviewState).toBe("current");
    expect(JSON.parse(String(result[0]?.sectorProfileSnapshot))).toMatchObject({ completenessPercent: 100 });
  });
});
