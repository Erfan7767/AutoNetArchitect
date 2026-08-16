import { beforeEach, describe, expect, it, vi } from "vitest";

const selectResults: unknown[][] = [];
const insertCalls: unknown[] = [];

const queryBuilder = () => {
  const builder: Record<string, (...args: unknown[]) => unknown> = {};
  builder.from = () => builder;
  builder.innerJoin = () => builder;
  builder.where = () => builder;
  builder.orderBy = () => builder;
  builder.limit = async () => selectResults.shift() || [];
  return builder;
};

const fakeDb = {
  select: vi.fn(() => queryBuilder()),
  insert: vi.fn(() => ({ values: (value: unknown) => { insertCalls.push(value); return Promise.resolve(); } })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { addConfigArtifact, recordAgentTeamAudit } = await import("./autonet");

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
      observedPlatform: "network_os",
      observedModel: "observed-model",
      observedVersion: "1.0.0",
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

  it.each(["Cisco", "Huawei", "Fortinet", "HPE Aruba"])("allows %s pass artifacts only with a persisted exact configuration-supported decision", async vendor => {
    const currentDevice = device(vendor);
    const assessment = {
      decision: "configuration_supported",
      observedVendor: vendor,
      observedPlatform: currentDevice.device.observedPlatform,
      observedModel: currentDevice.device.observedModel,
      observedVersion: currentDevice.device.observedVersion,
      capabilityEvidenceReference: currentDevice.device.capabilityEvidenceReference,
      licenseEvidenceReference: currentDevice.device.licenseEvidenceReference,
      configurationPathEvidenceReference: currentDevice.device.configurationPathEvidenceReference,
    };
    selectResults.push([project()], [currentDevice], [assessment], [project()], []);

    await addConfigArtifact(1, {
      deviceId: 10,
      vendor,
      deviceName: "observed-device",
      artifactSummary: "Exact reviewed capability path only.",
      artifactPreview: "redacted preview",
      featureGuard: "pass",
      unsupportedFeatureLog: "",
    }, actor);

    expect(insertCalls[0]).toMatchObject({ projectId: 1, deviceId: 10, featureGuard: "pass" });
  });

  it.each(["Cisco", "Huawei", "Fortinet", "HPE Aruba"])("blocks %s candidate and unsupported capability decisions before pass artifact storage", async vendor => {
    for (const decision of ["review_required", "unsupported"] as const) {
      const currentDevice = device(vendor);
      const assessment = {
        decision,
        observedVendor: vendor,
        observedPlatform: currentDevice.device.observedPlatform,
        observedModel: currentDevice.device.observedModel,
        observedVersion: currentDevice.device.observedVersion,
        capabilityEvidenceReference: currentDevice.device.capabilityEvidenceReference,
        licenseEvidenceReference: currentDevice.device.licenseEvidenceReference,
        configurationPathEvidenceReference: currentDevice.device.configurationPathEvidenceReference,
      };
      selectResults.push([project()], [currentDevice], [assessment]);

      await expect(addConfigArtifact(1, {
        deviceId: 10,
        vendor,
        deviceName: "observed-device",
        artifactSummary: "Capability decision remains non-authorizing.",
        artifactPreview: "",
        featureGuard: "pass",
        unsupportedFeatureLog: "",
      }, actor)).rejects.toThrow("accepted exact capability decision");
    }
    expect(insertCalls).toHaveLength(0);
  });

  it.each(["Cisco", "Huawei", "Fortinet", "HPE Aruba"])("blocks %s pass artifacts when device capability evidence is missing", async vendor => {
    const incomplete = device(vendor);
    incomplete.device.capabilityVerified = false;
    incomplete.device.licenseEvidenceReference = "";
    selectResults.push([project()], [incomplete]);

    await expect(addConfigArtifact(1, {
      deviceId: 10,
      vendor,
      deviceName: "observed-device",
      artifactSummary: "No exact evidence path.",
      artifactPreview: "",
      featureGuard: "pass",
      unsupportedFeatureLog: "",
    }, actor)).rejects.toThrow("requires exact capability, license, and configuration-path evidence references");
    expect(insertCalls).toHaveLength(0);
  });

  it("persists a redacted team evaluation without execution authority", async () => {
    selectResults.push([project()]);

    const result = await recordAgentTeamAudit(1, {
      productionExecutionPermitted: false,
      agents: [{ role: "authorized_discovery", state: "ready", blockers: [] }],
    }, actor);

    expect(result).toEqual({ recorded: true, productionExecutionPermitted: false });
    expect(insertCalls[0]).toMatchObject({ action: "multi_agent.workflow_evaluated" });
    expect(String(insertCalls[0])).not.toContain("credential_reference");
  });
});
