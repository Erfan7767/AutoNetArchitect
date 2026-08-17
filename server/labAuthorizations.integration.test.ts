import { beforeEach, describe, expect, it, vi } from "vitest";

const selectResults: unknown[][] = [];
const insertCalls: unknown[] = [];
const updateCalls: unknown[] = [];

function queryBuilder() {
  const builder: Record<string, (...args: unknown[]) => unknown> = {};
  builder.from = () => builder;
  builder.innerJoin = () => builder;
  builder.where = () => builder;
  builder.limit = async () => selectResults.shift() || [];
  builder.orderBy = async () => selectResults.shift() || [];
  return builder;
}

const fakeDb = {
  select: vi.fn(() => queryBuilder()),
  insert: vi.fn(() => ({ values: (value: unknown) => { insertCalls.push(value); return Promise.resolve(); } })),
  update: vi.fn(() => ({ set: (value: unknown) => ({ where: () => { updateCalls.push(value); return Promise.resolve(); } }) })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { recordVirtualTest } = await import("./autonet");

const actor = { id: 44, name: "Lab reviewer" };
const planRecord = { plan: { id: 80, projectId: 20, artifactHash: "artifact-hash-001", targetFactsHash: "facts-hash-001", scopeHash: "scope-hash-001", virtualValidationState: "test_queued" }, project: { id: 20, ownerId: 44 } };
const labDraft = { state: "test_passed" as const, adapterKind: "lab-validation", fidelityLabel: "vendor_image_lab", artifactHash: "artifact-hash-001", targetFactsHash: "facts-hash-001", scopeHash: "scope-hash-001", detail: "Isolated lab observations matched the approved golden checks." };

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  updateCalls.length = 0;
  vi.clearAllMocks();
});

describe("central laboratory authorization gate", () => {
  it("blocks vendor-image lab evidence without a written laboratory authorization identifier", async () => {
    selectResults.push([planRecord]);

    await expect(recordVirtualTest(20, 80, labDraft, actor)).rejects.toThrow("recorded written laboratory authorization");
    expect(insertCalls).toHaveLength(0);
    expect(updateCalls).toHaveLength(0);
  });

  it("accepts laboratory evidence only after a current authorization matches the exact change-plan scope", async () => {
    const authorization = { id: 51, projectId: 20, scopeHash: "scope-hash-001", approvedAt: new Date("2025-01-01T00:00:00Z"), expiresAt: new Date("2099-01-01T00:00:00Z"), environmentClass: "vendor_image_lab" };
    selectResults.push([planRecord], [authorization], [planRecord]);

    const result = await recordVirtualTest(20, 80, { ...labDraft, laboratoryAuthorizationId: 51 }, actor);

    expect(insertCalls[0]).toMatchObject({ changePlanId: 80, fidelityLabel: "vendor_image_lab", scopeHash: "scope-hash-001" });
    expect(updateCalls[0]).toMatchObject({ virtualValidationState: "test_passed" });
    expect(result).toMatchObject(planRecord);
  });
});
