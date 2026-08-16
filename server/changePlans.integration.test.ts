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
  builder.orderBy = () => builder;
  builder.then = (resolve: (value: unknown[]) => unknown, reject: (reason: unknown) => unknown) => Promise.resolve(selectResults.shift() || []).then(resolve, reject);
  return builder;
};

const fakeDb = {
  select: vi.fn(() => queryBuilder()),
  insert: vi.fn(() => ({
    values: (value: unknown) => {
      insertCalls.push(value);
      const promise = Promise.resolve();
      Object.assign(promise, { $returningId: async () => [{ id: 77 }] });
      return promise;
    },
  })),
  update: vi.fn(() => ({
    set: () => ({ where: async () => undefined }),
  })),
};

vi.mock("./db", () => ({ getDb: vi.fn(async () => fakeDb) }));

const { appRouter } = await import("./routers");

const actor = {
  id: 11,
  openId: "reviewer-open-id",
  email: "reviewer@example.test",
  name: "Reviewer",
  loginMethod: "test",
  role: "user" as const,
  createdAt: new Date(),
  updatedAt: new Date(),
  lastSignedIn: new Date(),
};

const enterpriseInputs = [
  "Business-service priorities and outage impact",
  "Site and management-network boundaries",
  "Identity, segmentation, and internet-edge policy",
  "Supported hardware, software, license, and support evidence",
  "Change authority and maintenance policy",
];

const context: TrpcContext = {
  user: actor,
  req: { protocol: "https", headers: {} } as TrpcContext["req"],
  res: {} as TrpcContext["res"],
};

function project(sectorProfile: string, inputs: string[], reviewedAt: Date | null) {
  return {
    id: 1,
    ownerId: actor.id,
    sectorProfile,
    sectorInputs: JSON.stringify(inputs),
    sectorInputsUpdatedAt: reviewedAt,
  };
}

const input = {
  projectId: 1,
  deviceId: 10,
  name: "Branch edge change",
  artifactHash: "artifact-hash",
  scopeHash: "scope-hash",
};

beforeEach(() => {
  selectResults.length = 0;
  insertCalls.length = 0;
  vi.clearAllMocks();
});

describe("projects.changePlans.create real integration path", () => {
  it.each([
    ["unselected", project("unselected", [], new Date())],
    ["incomplete", project("enterprise", [enterpriseInputs[0]], new Date())],
    ["stale", project("enterprise", enterpriseInputs, new Date(Date.now() - 91 * 24 * 60 * 60 * 1000))],
  ])("rejects %s sector state before persistence", async (_label, projectRecord) => {
    selectResults.push([projectRecord]);
    const caller = appRouter.createCaller(context);

    await expect(caller.projects.changePlans.create(input)).rejects.toThrow();
    expect(insertCalls).toHaveLength(0);
  });

  it("blocks observed facts when capability verification is unresolved", async () => {
    const reviewedAt = new Date();
    const projectRecord = project("enterprise", enterpriseInputs, reviewedAt);
    const deviceRecord = { device: { id: 10, factState: "observed", factsHash: "facts-hash", capabilityVerified: false }, project: projectRecord };
    selectResults.push([projectRecord], [deviceRecord]);
    const caller = appRouter.createCaller(context);

    await expect(caller.projects.changePlans.create(input)).rejects.toThrow("capability verification");
    expect(insertCalls).toHaveLength(0);
  });

  it.each([
    ["failed virtual validation", { state: "test_failed", observedAt: new Date(), scopeHash: "scope-hash" }, "Virtual validation state is test_failed."],
    ["stale virtual validation", { state: "test_passed", observedAt: new Date(Date.now() - 25 * 60 * 60 * 1000), scopeHash: "scope-hash" }, "Virtual-test evidence is stale."],
    ["out-of-scope virtual validation", { state: "test_passed", observedAt: new Date(), scopeHash: "other-scope" }, "Virtual-test scope does not match the requested change."],
  ])("blocks approval readiness for %s", async (_label, virtualTest, expectedBlocker) => {
    const now = new Date();
    const projectRecord = { ...project("enterprise", enterpriseInputs, now), requirementsComplete: 100 };
    const planRecord = {
      id: 55,
      projectId: 1,
      deviceId: 10,
      artifactHash: "artifact-hash",
      targetFactsHash: "facts-hash",
      scopeHash: "scope-hash",
      virtualValidationState: virtualTest.state,
      releaseState: "draft",
      backupVerified: false,
      maintenanceWindowValid: false,
    };
    const deviceRecord = {
      device: {
        id: 10,
        factState: "observed",
        factsHash: "facts-hash",
        capabilityVerified: true,
        capabilityEvidenceReference: "capability-evidence-1",
        licenseEvidenceReference: "license-evidence-1",
        configurationPathEvidenceReference: "configuration-path-evidence-1",
        lastObservedAt: now,
      },
      project: projectRecord,
    };
    const virtualTestRecord = { ...virtualTest, changePlanId: 55, artifactHash: "artifact-hash", targetFactsHash: "facts-hash", adapterKind: "test", fidelityLabel: "logical_intent_only", detail: "recorded" };
    selectResults.push([{ plan: planRecord, project: projectRecord }], [deviceRecord], [virtualTestRecord]);
    const caller = appRouter.createCaller(context);

    const result = await caller.projects.changePlans.approvalReadiness({ changePlanId: 55 });
    expect(result.decision.status).toBe("blocked");
    expect(result.decision.blockers).toContain(expectedBlocker);
  });

  it("blocks automatic upload and preserves the failed virtual-validation blocker", async () => {
    const now = new Date();
    const projectRecord = { ...project("enterprise", enterpriseInputs, now), requirementsComplete: 100 };
    const planRecord = {
      id: 55,
      projectId: 1,
      deviceId: 10,
      artifactHash: "artifact-hash",
      targetFactsHash: "facts-hash",
      scopeHash: "scope-hash",
      virtualValidationState: "test_failed",
      releaseState: "draft",
      backupVerified: false,
      maintenanceWindowValid: false,
    };
    const deviceRecord = {
      device: {
        id: 10,
        factState: "observed",
        factsHash: "facts-hash",
        capabilityVerified: true,
        lastObservedAt: now,
      },
      project: projectRecord,
    };
    const virtualTestRecord = { state: "test_failed", observedAt: now, artifactHash: "artifact-hash", targetFactsHash: "facts-hash", scopeHash: "scope-hash" };
    selectResults.push(
      [{ plan: planRecord, project: projectRecord }],
      [{ plan: planRecord, project: projectRecord }],
      [deviceRecord],
      [virtualTestRecord],
    );
    const caller = appRouter.createCaller(context);

    const result = await caller.projects.changePlans.prepareDeployment({ changePlanId: 55 });

    expect(result.status).toBe("blocked");
    expect(result.automaticUploadAllowed).toBe(false);
    expect(result.blockers).toContain("Virtual validation state is test_failed.");
    expect(result.requiredHumanAction).toContain("authorized human executor");
  });

  it("keeps automatic upload denied after all readiness evidence and human approval are recorded", async () => {
    const now = new Date();
    const projectRecord = { ...project("enterprise", enterpriseInputs, now), requirementsComplete: 100 };
    const planRecord = {
      id: 56,
      projectId: 1,
      deviceId: 10,
      artifactHash: "artifact-hash",
      targetFactsHash: "facts-hash",
      scopeHash: "scope-hash",
      virtualValidationState: "test_passed",
      releaseState: "approved",
      backupVerified: true,
      maintenanceWindowValid: true,
    };
    const deviceRecord = {
      device: {
        id: 10,
        factState: "observed",
        factsHash: "facts-hash",
        capabilityVerified: true,
        lastObservedAt: now,
      },
      project: projectRecord,
    };
    const virtualTestRecord = { state: "test_passed", observedAt: now, artifactHash: "artifact-hash", targetFactsHash: "facts-hash", scopeHash: "scope-hash" };
    selectResults.push(
      [{ plan: planRecord, project: projectRecord }],
      [{ plan: planRecord, project: projectRecord }],
      [deviceRecord],
      [virtualTestRecord],
    );
    const caller = appRouter.createCaller(context);

    const result = await caller.projects.changePlans.prepareDeployment({ changePlanId: 56 });

    expect(result.status).toBe("human_execution_required");
    expect(result.automaticUploadAllowed).toBe(false);
    expect(result.blockers).toEqual([]);
  });

  it("records an observed failed verification and flags human rollback review", async () => {
    const now = new Date();
    const projectRecord = { ...project("enterprise", enterpriseInputs, now), requirementsComplete: 100 };
    const planRecord = {
      id: 57,
      projectId: 1,
      releaseState: "approved",
      humanApprover: "Named approver",
    };
    const recordedVerification = {
      id: 1,
      changePlanId: 57,
      state: "failed",
      verificationType: "connectivity_verification",
      expectedOutcome: "Approved services remain reachable.",
      observedOutcome: "Observed loss of reachability after the externally performed change.",
      evidenceReference: "evidence://verification/57/1",
      rollbackReviewRequired: true,
      recordedBy: "Reviewer",
      observedAt: now,
      createdAt: now,
    };
    selectResults.push(
      [{ plan: planRecord, project: projectRecord }],
      [{ plan: planRecord, project: projectRecord }],
      [recordedVerification],
    );
    const caller = appRouter.createCaller(context);

    const result = await caller.projects.changePlans.postChangeVerification.record({
      changePlanId: 57,
      state: "failed",
      verificationType: "connectivity_verification",
      expectedOutcome: "Approved services remain reachable.",
      observedOutcome: "Observed loss of reachability after the externally performed change.",
      evidenceReference: "evidence://verification/57/1",
      observedAt: now,
    });

    expect(result).toEqual([recordedVerification]);
    const verificationInsert = insertCalls.find(value => typeof value === "object" && value !== null && "verificationType" in value) as Record<string, unknown> | undefined;
    expect(verificationInsert?.rollbackReviewRequired).toBe(true);
    expect(verificationInsert?.state).toBe("failed");
    expect(fakeDb.update).toHaveBeenCalledTimes(1);
  });

  it("refuses post-change evidence until a human change-plan approval is recorded", async () => {
    const now = new Date();
    const projectRecord = { ...project("enterprise", enterpriseInputs, now), requirementsComplete: 100 };
    const planRecord = { id: 58, projectId: 1, releaseState: "ready_for_approval", humanApprover: null };
    selectResults.push([{ plan: planRecord, project: projectRecord }]);
    const caller = appRouter.createCaller(context);

    await expect(caller.projects.changePlans.postChangeVerification.record({
      changePlanId: 58,
      state: "passed",
      verificationType: "connectivity_verification",
      expectedOutcome: "Approved services remain reachable.",
      observedOutcome: "Observed reachability evidence was supplied.",
      evidenceReference: "evidence://verification/58/1",
      observedAt: now,
    })).rejects.toThrow("recorded human change-plan approval");
  });

  it("persists and returns sector snapshot fields for a complete current state", async () => {
    const reviewedAt = new Date();
    const projectRecord = project("enterprise", enterpriseInputs, reviewedAt);
    const deviceRecord = {
      device: {
        id: 10,
        factState: "observed",
        factsHash: "facts-hash",
        capabilityVerified: true,
        capabilityEvidenceReference: "capability-evidence-1",
        licenseEvidenceReference: "license-evidence-1",
        configurationPathEvidenceReference: "configuration-path-evidence-1",
      },
      project: projectRecord,
    };
    const persistedPlan = {
      ...input,
      id: 77,
      targetFactsHash: "facts-hash",
      virtualValidationState: "not_tested",
      releaseState: "draft",
      sectorProfileSnapshot: JSON.stringify({ profileId: "enterprise", completenessPercent: 100 }),
      sectorInputsHash: "b".repeat(64),
      sectorReviewState: "current",
      sectorReviewedAt: reviewedAt,
    };
    selectResults.push([projectRecord], [deviceRecord], [projectRecord], [persistedPlan]);
    const caller = appRouter.createCaller(context);

    const result = await caller.projects.changePlans.create(input);

    const planInsert = insertCalls.find(value => typeof value === "object" && value !== null && "sectorProfileSnapshot" in value) as Record<string, unknown> | undefined;
    expect(planInsert?.sectorReviewState).toBe("current");
    expect(planInsert?.sectorInputsHash).toMatch(/^[a-f0-9]{64}$/);
    expect(result[0]?.sectorReviewState).toBe("current");
    expect(JSON.parse(String(result[0]?.sectorProfileSnapshot))).toMatchObject({ completenessPercent: 100 });
  });
});
