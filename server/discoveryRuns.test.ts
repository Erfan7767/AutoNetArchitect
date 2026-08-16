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

const { createDiscoveryRun, enrollSiteAgent, listDiscoveryRuns, transitionDiscoveryRun } = await import("./autonet");

const actor = { id: 11, name: "Reviewer", email: "reviewer@example.test" };
const queuedRun = {
  id: 42,
  siteId: 7,
  discoveryScopeId: 55,
  mode: "read_only",
  state: "queued",
  scopeHash: "scope-hash-123",
  evidenceSummary: "Sensitive details were redacted.",
  evidenceHash: "evidence-hash",
  ambiguousCount: 1,
  unsupportedCount: 0,
};

const activeScope = {
  id: 55,
  projectId: 1,
  siteId: 7,
  scopeReference: "scope-ref-hq/discovery-01",
  targetAllowlist: "10.0.0.10",
  cidrAllowlist: "10.0.0.0/24",
  protocolAllowlist: "ssh,netconf",
  scopeHash: "scope-hash-123",
  status: "active",
};

beforeEach(() => {
  selectResults.length = 0;
  updateCalls.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("discovery run persistence contracts", () => {
  it("creates a read-only run and persists redacted evidence", async () => {
    selectResults.push([{ id: 7 }], [{ scope: activeScope }], [{ run: queuedRun, projectId: 1 }]);

    const result = await createDiscoveryRun(1, {
      siteId: 7,
      discoveryScopeId: 55,
      evidenceSummary: "token: do-not-store",
      evidenceHash: "evidence-hash",
      ambiguousCount: 1,
    }, actor);

    expect(result?.run.state).toBe("queued");
    expect(result?.run.mode).toBe("read_only");
    expect(insertCalls[0]).toMatchObject({ discoveryScopeId: 55, scopeHash: "scope-hash-123", evidenceSummary: "Sensitive details were redacted." });
  });

  it("rejects creation when the site is not owned by the project actor", async () => {
    selectResults.push([]);

    await expect(createDiscoveryRun(1, { siteId: 99, discoveryScopeId: 55 }, actor)).resolves.toBeUndefined();
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

  it("enrolls an agent only for the exact approved site scope and retains read-only mode", async () => {
    const site = { id: 7, projectId: 1, approvedScopeReference: "scope-ref-hq", mode: "read_only", enrollmentState: "not_enrolled" };
    selectResults.push([{ site, project: { id: 1, ownerId: actor.id } }], [{ id: 1 }], [{ ...site, enrollmentState: "active", agentReference: "site-agent-hq" }]);

    const result = await enrollSiteAgent(1, 7, { agentReference: "site-agent-hq", approvedScopeReference: "scope-ref-hq" }, actor);

    expect(result?.[0]).toMatchObject({ enrollmentState: "active", agentReference: "site-agent-hq", mode: "read_only" });
    expect(updateCalls[0]).toMatchObject({ agentReference: "site-agent-hq", enrollmentState: "active", mode: "read_only" });
  });

  it("rejects agent enrollment when the submitted scope reference differs", async () => {
    const site = { id: 7, projectId: 1, approvedScopeReference: "scope-ref-hq", mode: "read_only", enrollmentState: "not_enrolled" };
    selectResults.push([{ site, project: { id: 1, ownerId: actor.id } }]);

    await expect(enrollSiteAgent(1, 7, { agentReference: "site-agent-hq", approvedScopeReference: "different-scope" }, actor)).rejects.toThrow("exact approved scope reference");
    expect(updateCalls).toHaveLength(0);
  });
});
