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
      Object.assign(promise, { $returningId: async () => [{ id: 91 }] });
      return promise;
    },
  })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { appRouter } = await import("./routers");

function context(): TrpcContext {
  return {
    user: { id: 61, openId: "scope-user", email: "scope@example.test", name: "Scope reviewer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const activeSite = {
  id: 7,
  projectId: 13,
  name: "HQ",
  approvedScopeReference: "approval-hq-2026-08",
  enrollmentState: "active",
  mode: "read_only",
};

const storedScope = {
  id: 55,
  projectId: 13,
  siteId: 7,
  scopeReference: "approval-hq-2026-08/discovery-01",
  targetAllowlist: "10.0.0.10",
  cidrAllowlist: "10.0.0.0/24",
  protocolAllowlist: "ssh,netconf",
  scopeHash: "approved-scope-hash-01",
  status: "active",
};

const linkedRun = {
  id: 91,
  siteId: 7,
  discoveryScopeId: 55,
  scopeHash: "approved-scope-hash-01",
  mode: "read_only",
  state: "queued",
  evidenceSummary: "Queued for authorized read-only collection.",
  ambiguousCount: 0,
  unsupportedCount: 0,
};

const scopeInput = {
  projectId: 13,
  siteId: 7,
  scopeReference: "approval-hq-2026-08/discovery-01",
  targetAllowlist: "10.0.0.10",
  cidrAllowlist: "10.0.0.0/24",
  protocolAllowlist: "ssh,netconf",
  scopeHash: "approved-scope-hash-01",
};

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("authorized discovery scope integration", () => {
  it("records a bounded active scope and links a queued read-only run to that saved scope", async () => {
    const caller = appRouter.createCaller(context());
    const ownedSite = { site: activeSite, project: { id: 13, ownerId: 61 } };
    selectResults.push([ownedSite], [ownedSite], [storedScope]);

    const scopes = await caller.projects.discoveryScopes.create(scopeInput);

    expect(scopes).toEqual([storedScope]);
    expect(insertCalls[0]).toMatchObject({ siteId: 7, targetAllowlist: "10.0.0.10", cidrAllowlist: "10.0.0.0/24", protocolAllowlist: "ssh,netconf", status: "active" });

    selectResults.push([{ id: 7 }], [{ scope: storedScope }], [{ run: linkedRun, projectId: 13 }]);
    const run = await caller.projects.discoveryRuns.create({ projectId: 13, siteId: 7, discoveryScopeId: 55, evidenceSummary: "Queued for authorized read-only collection." });

    expect(run?.run).toMatchObject({ id: 91, discoveryScopeId: 55, scopeHash: "approved-scope-hash-01", mode: "read_only", state: "queued" });
    expect(insertCalls.find(value => typeof value === "object" && value !== null && "discoveryScopeId" in value)).toMatchObject({ discoveryScopeId: 55, scopeHash: "approved-scope-hash-01", mode: "read_only" });
  });

  it("rejects a scope without an explicit target or CIDR allowlist", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([{ site: activeSite, project: { id: 13, ownerId: 61 } }]);

    await expect(caller.projects.discoveryScopes.create({ ...scopeInput, targetAllowlist: "", cidrAllowlist: "" })).rejects.toThrow("target or CIDR allowlist");
    expect(insertCalls).toHaveLength(0);
  });

  it("rejects discovery run creation when the requested saved scope is not active for the selected site", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([{ id: 7 }], []);

    await expect(caller.projects.discoveryRuns.create({ projectId: 13, siteId: 7, discoveryScopeId: 999 })).rejects.toThrow("saved active authorized scope");
    expect(insertCalls).toHaveLength(0);
  });
});
