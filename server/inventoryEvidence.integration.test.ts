import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TrpcContext } from "./_core/context";

const selectResults: unknown[][] = [];
const updateCalls: unknown[] = [];
const insertCalls: unknown[] = [];

const queryBuilder = () => {
  const builder: Record<string, (...args: unknown[]) => unknown> = {};
  builder.from = () => builder;
  builder.innerJoin = () => builder;
  builder.where = () => builder;
  builder.limit = async () => selectResults.shift() || [];
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
    user: { id: 61, openId: "inventory-user", email: "inventory@example.test", name: "Inventory reviewer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const managedDevice = {
  id: 21,
  siteId: 7,
  deviceReference: "edge-fw-01",
  managementAddress: "10.0.0.10",
  protocol: "https_api",
  factState: "unobserved",
  discoveryRunId: 0,
  discoveryScopeId: 0,
};

const ownedDeviceRecord = { device: managedDevice, site: { id: 7, projectId: 13 }, project: { id: 13, ownerId: 61 } };
const validScope = { id: 55, projectId: 13, siteId: 7, scopeHash: "approved-scope-hash-01", status: "active" };
const completedRun = { id: 77, siteId: 7, discoveryScopeId: 55, state: "completed", mode: "read_only" };

const observationInput = {
  projectId: 13,
  deviceId: 21,
  discoveryRunId: 77,
  discoveryScopeId: 55,
  observedVendor: "Fortinet",
  observedPlatform: "FortiOS",
  observedModel: "FG-100F",
  observedVersion: "7.4.0",
  factsHash: "observed-facts-hash-01",
  factState: "observed" as const,
  capabilityVerified: false,
};

beforeEach(() => {
  selectResults.length = 0;
  updateCalls.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("scoped inventory evidence integration", () => {
  it("records observed inventory only when the evidence is tied to a completed site run and saved scope", async () => {
    selectResults.push([ownedDeviceRecord], [{ run: completedRun, scope: validScope }], [{ ...ownedDeviceRecord, device: { ...managedDevice, ...observationInput } }]);
    const caller = appRouter.createCaller(context());

    const result = await caller.projects.devices.recordObservation(observationInput);

    expect(result?.device).toMatchObject({ id: 21, siteId: 7, discoveryRunId: 77, discoveryScopeId: 55, factState: "observed" });
    expect(updateCalls[0]).toMatchObject({ discoveryRunId: 77, discoveryScopeId: 55, observedVendor: "Fortinet", factsHash: "observed-facts-hash-01" });
    expect(insertCalls).toHaveLength(1);
  });

  it("rejects evidence from a run or scope that is not authorized for the device site", async () => {
    selectResults.push([ownedDeviceRecord], []);
    const caller = appRouter.createCaller(context());

    await expect(caller.projects.devices.recordObservation({ ...observationInput, discoveryScopeId: 999 })).rejects.toThrow("authorized for the device site");
    expect(updateCalls).toHaveLength(0);
  });

  it("rejects inventory evidence from a queued discovery run", async () => {
    selectResults.push([ownedDeviceRecord], [{ run: { ...completedRun, state: "queued" }, scope: validScope }]);
    const caller = appRouter.createCaller(context());

    await expect(caller.projects.devices.recordObservation(observationInput)).rejects.toThrow("completed or partial read-only discovery run");
    expect(updateCalls).toHaveLength(0);
  });
});
