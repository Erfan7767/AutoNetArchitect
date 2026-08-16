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
  insert: vi.fn(() => ({ values: (value: unknown) => { insertCalls.push(value); return Promise.resolve(); } })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { appRouter } = await import("./routers");

function context(): TrpcContext {
  return {
    user: { id: 71, openId: "rollback-reviewer", email: "rollback@example.test", name: "Rollback reviewer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const project = { id: 4, ownerId: 71, name: "Scoped rollback project" };
const plan = { id: 41, projectId: 4, backupVerified: true, targetFactsHash: "facts-hash-123", scopeHash: "scope-hash-123" };
const input = {
  changePlanId: 41,
  rollbackScopeReference: "Scoped interface and routing rollback review",
  rollbackArtifactHash: "rollback-artifact-hash-123",
  targetFactsHash: "facts-hash-123",
  scopeHash: "scope-hash-123",
  backupEvidenceReference: "backup-evidence-reference",
  trigger: "Observed verification failure requires human rollback decision",
  reviewState: "review_required" as const,
};

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("rollback review integration", () => {
  it("records a hash-bound rollback review without automatic execution authority", async () => {
    const caller = appRouter.createCaller(context());
    const stored = { id: 7, ...input, automaticExecutionPermitted: false, humanReviewer: "Rollback reviewer" };
    selectResults.push([{ plan, project }], [{ plan, project }], [stored]);

    const reviews = await caller.projects.changePlans.rollbackReview.record(input);

    expect(insertCalls[0]).toMatchObject({ changePlanId: 41, automaticExecutionPermitted: false, targetFactsHash: "facts-hash-123", scopeHash: "scope-hash-123" });
    expect(reviews).toEqual([stored]);
  });

  it("rejects a mismatched rollback scope before writing a review", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([{ plan, project }]);

    await expect(caller.projects.changePlans.rollbackReview.record({ ...input, scopeHash: "different-scope-hash" })).rejects.toThrow("exactly match");
    expect(insertCalls).toHaveLength(0);
  });

  it("requires a verified backup before accepting a rollback review", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([{ plan: { ...plan, backupVerified: false }, project }]);

    await expect(caller.projects.changePlans.rollbackReview.record(input)).rejects.toThrow("verified backup");
    expect(insertCalls).toHaveLength(0);
  });
});
