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
  builder.orderBy = () => builder;
  builder.then = (resolve: (value: unknown[]) => unknown, reject: (reason: unknown) => unknown) => Promise.resolve(selectResults.shift() || []).then(resolve, reject);
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
    user: { id: 75, openId: "rollback-preparer", email: "preparer@example.test", name: "External rollback preparer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const project = { id: 6, ownerId: 75, name: "External rollback project" };
const plan = { id: 45, projectId: 6, backupVerified: true, targetFactsHash: "facts-hash-789", scopeHash: "scope-hash-789" };
const review = { id: 17, changePlanId: 45, reviewState: "reviewed", rollbackArtifactHash: "rollback-artifact-hash-789" };
const verification = { id: 2, changePlanId: 45, rollbackReviewRequired: true, state: "failed" };
const backup = { id: 5, changePlanId: 45, verificationState: "verified", targetFactsHash: "facts-hash-789", scopeHash: "scope-hash-789", automaticCapturePermitted: false };
const eligibility = { id: 8, deviceId: 10, rollbackArtifactHash: "rollback-artifact-hash-789", targetFactsHash: "facts-hash-789", scopeHash: "scope-hash-789", decision: "eligible" };
const input = { changePlanId: 45, rollbackReviewId: 17, rollbackArtifactHash: "rollback-artifact-hash-789", targetFactsHash: "facts-hash-789", scopeHash: "scope-hash-789" };

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("scoped rollback preparation integration", () => {
  it("prepares only a human-controlled external packet after every evidence gate matches", async () => {
    const caller = appRouter.createCaller(context());
    const stored = { id: 9, ...input, eligibilityState: "ready_for_human_execution", humanExecutionRequired: true, automaticExecutionPermitted: false, preparedBy: "External rollback preparer" };
    selectResults.push([{ plan, project }], [review], [verification], [backup], [eligibility], [{ plan, project }], [stored]);

    const preparations = await caller.projects.changePlans.rollbackPreparation.prepare(input);

    expect(insertCalls[0]).toMatchObject({ changePlanId: 45, eligibilityState: "ready_for_human_execution", humanExecutionRequired: true, automaticExecutionPermitted: false });
    expect(preparations).toEqual([stored]);
  });

  it("blocks preparation until a reviewed rollback record exists", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([{ plan, project }], [{ ...review, reviewState: "review_required" }]);

    await expect(caller.projects.changePlans.rollbackPreparation.prepare(input)).rejects.toThrow("human-reviewed rollback review");
    expect(insertCalls).toHaveLength(0);
  });

  it("blocks preparation until a matching externally verified backup receipt exists", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([{ plan, project }], [review], [verification], []);

    await expect(caller.projects.changePlans.rollbackPreparation.prepare(input)).rejects.toThrow("verified external backup receipt");
    expect(insertCalls).toHaveLength(0);
  });

  it("blocks a rollback artifact that differs from the reviewed scoped artifact", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([{ plan, project }], [review], [verification], [backup], [eligibility]);

    await expect(caller.projects.changePlans.rollbackPreparation.prepare({ ...input, rollbackArtifactHash: "different-artifact-hash" })).rejects.toThrow("action-specific rollback eligibility");
    expect(insertCalls).toHaveLength(0);
  });

  it("blocks preparation when the device action path has no eligible rollback decision", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([{ plan, project }], [review], [verification], [backup], [{ ...eligibility, decision: "review_required" }]);

    await expect(caller.projects.changePlans.rollbackPreparation.prepare(input)).rejects.toThrow("action-specific rollback eligibility");
    expect(insertCalls).toHaveLength(0);
  });
});
