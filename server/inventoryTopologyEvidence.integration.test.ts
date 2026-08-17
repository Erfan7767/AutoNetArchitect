import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TrpcContext } from "./_core/context";

const selectResults: unknown[][] = [];
const insertCalls: unknown[] = [];

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
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { appRouter } = await import("./routers");

function context(): TrpcContext {
  return {
    user: { id: 44, openId: "topology-user", email: "topology@example.test", name: "Topology reviewer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const project = { id: 31, ownerId: 44, name: "Scoped topology" };
const observedDevice = { id: 71, siteId: 8, deviceReference: "dist-01", factState: "observed" };
const observedPeer = { id: 72, siteId: 8, deviceReference: "access-01", factState: "observed" };
const deviceRecord = (device: typeof observedDevice) => ({ device, site: { id: 8, projectId: 31 }, project });
const completedSource = { run: { id: 91, siteId: 8, discoveryScopeId: 19, state: "completed", mode: "read_only" }, scope: { id: 19, siteId: 8, projectId: 31, status: "active" } };
const interfaceInput = { projectId: 31, deviceId: 71, discoveryRunId: 91, discoveryScopeId: 19, interfaceReference: "GigabitEthernet1/0/1", state: "observed" as const, evidenceReference: "lldp-neighbor-record-91", evidenceHash: "evidence-hash-interface-91", inferenceRationale: "", observedAt: new Date("2026-08-17T00:00:00Z") };

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("inventory interface and topology evidence integration", () => {
  it("records an observed interface only with an observed device and completed authorized discovery source", async () => {
    const caller = appRouter.createCaller(context());
    const stored = { id: 1, ...interfaceInput, siteId: 8, deviceId: 71 };
    selectResults.push([deviceRecord(observedDevice)], [completedSource], [project], [{ evidence: stored, device: observedDevice, siteName: "HQ" }]);

    const evidence = await caller.projects.devices.interfaceEvidence.record(interfaceInput);

    expect(insertCalls[0]).toMatchObject({ deviceId: 71, state: "observed", interfaceReference: "GigabitEthernet1/0/1" });
    expect(evidence[0].evidence).toMatchObject({ state: "observed", discoveryRunId: 91, discoveryScopeId: 19 });
  });

  it("requires an explicit rationale for inferred interface topology", async () => {
    const caller = appRouter.createCaller(context());
    selectResults.push([deviceRecord(observedDevice)], [completedSource]);

    await expect(caller.projects.devices.interfaceEvidence.record({ ...interfaceInput, state: "inferred", inferenceRationale: "" })).rejects.toThrow("explicit inference rationale");
    expect(insertCalls).toHaveLength(0);
  });

  it("permits an explicitly unknown remote peer but prevents it from being labelled observed topology", async () => {
    const caller = appRouter.createCaller(context());
    const input = { projectId: 31, discoveryRunId: 91, discoveryScopeId: 19, endpointADeviceId: 71, endpointAInterfaceReference: "GigabitEthernet1/0/1", endpointBDeviceId: 0, endpointBInterfaceReference: "unknown remote peer", topologyState: "unknown" as const, evidenceReference: "local-link-signal-91", evidenceHash: "evidence-hash-link-91", inferenceRationale: "", observedAt: new Date("2026-08-17T00:00:00Z") };
    const stored = { id: 2, ...input, siteId: 8 };
    selectResults.push([deviceRecord(observedDevice)], [completedSource], [project], [{ evidence: stored, siteName: "HQ" }]);

    const evidence = await caller.projects.devices.linkEvidence.record(input);

    expect(insertCalls[0]).toMatchObject({ endpointADeviceId: 71, endpointBDeviceId: 0, topologyState: "unknown" });
    expect(evidence[0].evidence).toMatchObject({ topologyState: "unknown", endpointBInterfaceReference: "unknown remote peer" });
  });

  it("rejects an observed topology claim unless both owned endpoints are observed", async () => {
    const caller = appRouter.createCaller(context());
    const input = { projectId: 31, discoveryRunId: 91, discoveryScopeId: 19, endpointADeviceId: 71, endpointAInterfaceReference: "GigabitEthernet1/0/1", endpointBDeviceId: 72, endpointBInterfaceReference: "GigabitEthernet1/0/24", topologyState: "observed" as const, evidenceReference: "bidirectional-neighbor-record-91", evidenceHash: "evidence-hash-link-92", inferenceRationale: "", observedAt: new Date("2026-08-17T00:00:00Z") };
    selectResults.push([deviceRecord(observedDevice)], [completedSource], [deviceRecord({ ...observedPeer, factState: "ambiguous" })]);

    await expect(caller.projects.devices.linkEvidence.record(input)).rejects.toThrow("two observed endpoint devices");
    expect(insertCalls).toHaveLength(0);
  });
});
