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
      return Promise.resolve();
    },
  })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { appRouter } = await import("./routers");

function context(): TrpcContext {
  return {
    user: { id: 52, openId: "multisite-user", email: "multisite@example.test", name: "Business reviewer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const project = { id: 13, ownerId: 52, name: "Multi-site bank" };
const input = {
  projectId: 13,
  siteReference: "Branch-Riyadh-01",
  branchRole: "Transaction branch",
  servicePriorities: "Customer transactions and staff operations",
  availabilityObjective: "Human-approved availability objective pending service owner review",
  jurisdictionConstraints: "Human-supplied jurisdiction and data-residency constraints",
  humanMandatoryFields: ["Service owner", "Local access contact"],
  reviewState: "reviewed" as const,
};

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("multi-site business requirements integration", () => {
  it("records human-supplied branch requirements and returns parsed mandatory fields", async () => {
    const caller = appRouter.createCaller(context());
    const stored = { id: 9, projectId: 13, ...input, humanMandatoryFields: JSON.stringify(input.humanMandatoryFields), reviewedAt: new Date() };
    selectResults.push([project], [project], [stored]);

    const records = await caller.projects.siteBusinessRequirements.record(input);

    expect(insertCalls[0]).toMatchObject({ projectId: 13, siteReference: "Branch-Riyadh-01", reviewState: "reviewed" });
    expect(records[0]).toMatchObject({ siteReference: "Branch-Riyadh-01", humanMandatoryFields: ["Service owner", "Local access contact"] });
  });

  it("rejects a reviewed record when named human mandatory fields are absent", async () => {
    const caller = appRouter.createCaller(context());

    await expect(caller.projects.siteBusinessRequirements.record({ ...input, humanMandatoryFields: [] })).rejects.toThrow();
    expect(insertCalls).toHaveLength(0);
  });
});
