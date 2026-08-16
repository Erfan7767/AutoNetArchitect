import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TrpcContext } from "./_core/context";

const selectResults: unknown[][] = [];
const insertCalls: unknown[] = [];
const updateCalls: unknown[] = [];

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
  update: vi.fn(() => ({ set: (value: unknown) => { updateCalls.push(value); return { where: async () => undefined }; } })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { appRouter } = await import("./routers");

function context(): TrpcContext {
  return {
    user: { id: 73, openId: "backup-reviewer", email: "backup@example.test", name: "Backup reviewer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const project = { id: 5, ownerId: 73, name: "Backup receipt project" };
const plan = { id: 44, projectId: 5, backupVerified: false, targetFactsHash: "facts-hash-456", scopeHash: "scope-hash-456" };
const input = {
  changePlanId: 44,
  backupReference: "external-backup-receipt-44",
  backupArtifactHash: "backup-artifact-hash-456",
  targetFactsHash: "facts-hash-456",
  scopeHash: "scope-hash-456",
  verificationState: "verified" as const,
};

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  updateCalls.length = 0;
  vi.clearAllMocks();
});

describe("backup receipt integration", () => {
  it("records a verified external backup receipt and sets the plan gate from that receipt only", async () => {
    const caller = appRouter.createCaller(context());
    const stored = { id: 8, ...input, automaticCapturePermitted: false, humanVerifier: "Backup reviewer" };
    selectResults.push([{ plan, project }], [{ plan, project }], [stored]);

    const receipts = await caller.projects.changePlans.backupReceipts.record(input);

    expect(insertCalls[0]).toMatchObject({ changePlanId: 44, automaticCapturePermitted: false, verificationState: "verified" });
    expect(updateCalls[0]).toMatchObject({ backupVerified: true });
    expect(receipts).toEqual([stored]);
  });

  it("refuses a backup receipt whose target facts or scope does not match the plan", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([{ plan, project }]);

    await expect(caller.projects.changePlans.backupReceipts.record({ ...input, targetFactsHash: "different-facts-hash" })).rejects.toThrow("exactly match");
    expect(insertCalls).toHaveLength(0);
    expect(updateCalls).toHaveLength(0);
  });
});
