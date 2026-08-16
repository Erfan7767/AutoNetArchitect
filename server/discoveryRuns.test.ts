import { beforeEach, describe, expect, it, vi } from "vitest";

const selectResults: unknown[][] = [];
const updateCalls: unknown[] = [];
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
      Object.assign(promise, { $returningId: async () => [{ id: 42 }] });
      return promise;
    },
  })),
  update: vi.fn(() => ({
    set: (value: unknown) => {
      updateCalls.push(value);
      return { where: async () => undefined };
    },
  })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { createDiscoveryRun, listDiscoveryRuns, transitionDiscoveryRun } = await import("./autonet");

const actor = { id: 11, name: "Reviewer", email: "reviewer@example.test" };
const queuedRun = {
  id: 42,
  siteId: 7,
  mode: "read_only",
  state: "queued",
  scopeHash: "scope-hash-123",
  evidenceSummary: "Sensitive details were redacted.",
  evidenceHash: "evidence-hash",
  ambiguousCount: 1,
  unsupportedCount: 0,
};

beforeEach(() => {
  selectResults.length = 0;
  updateCalls.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("discovery run persistence contracts", () => {
  it("creates a read-only run and persists redacted evidence", async () => {
    selectResults.push([{ id: 7 }], [{ run: queuedRun, projectId: 1 }]);

    const result = await createDiscoveryRun(1, {
      siteId: 7,
      scopeHash: "scope-hash-123",
      evidenceSummary: "token: do-not-store",
      evidenceHash: "evidence-hash",
      ambiguousCount: 1,
    }, actor);

    expect(result?.run.state).toBe("queued");
    expect(result?.run.mode).toBe("read_only");
    expect(insertCalls[0]).toMatchObject({ evidenceSummary: "Sensitive details were redacted." });
  });

  it("rejects creation when the site is not owned by the project actor", async () => {
    selectResults.push([]);

    await expect(createDiscoveryRun(1, { siteId: 99, scopeHash: "scope-hash-123" }, actor)).resolves.toBeUndefined();
    expect(insertCalls).toHaveLength(0);
  });

  it("lists runs only after project ownership is established", async () => {
    selectResults.push([{ id: 1 }], [{ run: queuedRun, siteName: "HQ" }]);

    const result = await listDiscoveryRuns(1, actor.id);

    expect(result).toHaveLength(1);
    expect(result?.[0]?.run.evidenceSummary).toBe("Sensitive details were redacted.");
  });

  it("persists a valid state transition and rejects a terminal-state transition", async () => {
    selectResults.push([{ run: queuedRun, projectId: 1 }], [{ run: { ...queuedRun, state: "running" }, projectId: 1 }]);

    const result = await transitionDiscoveryRun(42, "running", { evidenceSummary: "Observed 4 devices." }, actor);

    expect(result?.run.state).toBe("running");
    expect(updateCalls[0]).toMatchObject({ state: "running", evidenceSummary: "Observed 4 devices." });

    selectResults.push([{ run: { ...queuedRun, state: "completed" }, projectId: 1 }]);
    await expect(transitionDiscoveryRun(42, "running", {}, actor)).rejects.toThrow("Invalid discovery-run transition");
  });
});
