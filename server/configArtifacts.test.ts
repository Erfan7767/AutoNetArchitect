import { beforeEach, describe, expect, it, vi } from "vitest";

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

const { addConfigArtifact } = await import("./autonet");

const actor = { id: 7, name: "Engineer", email: "engineer@example.test" };

function project() {
  return { id: 1, ownerId: actor.id };
}

function device(vendor: string) {
  return {
    device: {
      id: 10,
      factState: "observed",
      factsHash: "facts-hash",
      observedVendor: vendor,
      capabilityVerified: true,
      capabilityEvidenceReference: "capability-evidence",
      licenseEvidenceReference: "license-evidence",
      configurationPathEvidenceReference: "path-evidence",
    },
    project: project(),
  };
}

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("config artifact capability gate", () => {
  it.each(["Cisco", "Huawei", "Fortinet", "HPE Aruba"])("blocks %s pass artifacts without an accepted exact capability decision", async vendor => {
    selectResults.push([project()], [device(vendor)]);

    await expect(addConfigArtifact(1, {
      deviceId: 10,
      vendor,
      deviceName: "observed-device",
      artifactSummary: "Reference-only artifact.",
      artifactPreview: "redacted preview",
      featureGuard: "pass",
      unsupportedFeatureLog: "",
    }, actor)).rejects.toThrow("accepted exact capability decision");
    expect(insertCalls).toHaveLength(0);
  });

  it("allows a blocked artifact to be recorded as safe-refusal evidence", async () => {
    selectResults.push([project()], [device("Cisco")], [project()], []);

    await addConfigArtifact(1, {
      deviceId: 10,
      vendor: "Cisco",
      deviceName: "observed-device",
      artifactSummary: "Capability evidence did not authorize generation.",
      artifactPreview: "",
      featureGuard: "blocked",
      unsupportedFeatureLog: "Candidate release requires exact reviewed policy.",
    }, actor);

    expect(insertCalls[0]).toMatchObject({ projectId: 1, deviceId: 10, featureGuard: "blocked" });
  });
});
