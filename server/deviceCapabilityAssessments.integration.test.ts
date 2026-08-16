import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TrpcContext } from "./_core/context";

const selectResults: unknown[][] = [];
const insertCalls: unknown[] = [];

const queryBuilder = () => {
  const builder: Record<string, (...args: unknown[]) => unknown> = {};
  builder.from = () => builder;
  builder.innerJoin = () => builder;
  builder.where = () => builder;
  builder.orderBy = () => builder;
  builder.limit = async () => selectResults.shift() || [];
  builder.then = (resolve: (value: unknown[]) => unknown) => Promise.resolve(selectResults.shift() || []).then(resolve);
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
    user: { id: 61, openId: "capability-user", email: "capability@example.test", name: "Capability reviewer", loginMethod: "manus", role: "user", createdAt: new Date(), updatedAt: new Date(), lastSignedIn: new Date() },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

const ownedProject = () => ({ id: 13, ownerId: 61 });
function deviceRecord(vendor: string) {
  return {
    device: {
      id: 21,
      factState: "observed",
      factsHash: "observed-facts-hash",
      observedVendor: vendor,
      observedPlatform: "network_os",
      observedModel: "observed-model",
      observedVersion: "1.0.0",
      capabilityEvidenceReference: "capability-evidence",
      licenseEvidenceReference: "license-evidence",
      configurationPathEvidenceReference: "path-evidence",
    },
    project: ownedProject(),
  };
}

function input(vendor: string) {
  return {
    projectId: 13,
    deviceId: 21,
    observedVendor: vendor,
    observedPlatform: "network_os",
    observedModel: "observed-model",
    observedVersion: "1.0.0",
    capabilityEvidenceReference: "capability-evidence",
    licenseEvidenceReference: "license-evidence",
    configurationPathEvidenceReference: "path-evidence",
    decision: "configuration_supported" as const,
    assessedAt: new Date(),
  };
}

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("projects.devices exact capability assessment integration", () => {
  it.each(["Cisco", "Huawei", "Fortinet", "HPE Aruba"])("records an exact configuration-supported decision for observed %s evidence", async vendor => {
    const now = new Date();
    const stored = { id: 1, deviceId: 21, ...input(vendor), assessedAt: now, createdAt: now };
    selectResults.push([deviceRecord(vendor)], [deviceRecord(vendor)], [stored]);
    const caller = appRouter.createCaller(context());

    const result = await caller.projects.devices.recordCapabilityAssessment(input(vendor));

    expect(result).toEqual([stored]);
    expect(insertCalls.find(value => typeof value === "object" && value !== null && "decision" in value)).toMatchObject({ deviceId: 21, decision: "configuration_supported", observedVendor: vendor });
  });

  it("blocks an assessment that does not match the observed model", async () => {
    selectResults.push([deviceRecord("Cisco")]);
    const caller = appRouter.createCaller(context());

    await expect(caller.projects.devices.recordCapabilityAssessment({ ...input("Cisco"), observedModel: "different-model" })).rejects.toThrow("must match the observed vendor, platform, model, and version");
    expect(insertCalls).toHaveLength(0);
  });

  it("refuses list access for a device outside the caller project ownership", async () => {
    selectResults.push([]);
    const caller = appRouter.createCaller(context());
    await expect(caller.projects.devices.listCapabilityAssessments({ projectId: 999, deviceId: 21 })).rejects.toThrow();
  });
});
