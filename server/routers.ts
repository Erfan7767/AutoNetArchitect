import { TRPCError } from "@trpc/server";
import { z } from "zod";
import {
  approveDeployment,
  createChangePlan,
  createDiscoveryRun,
  createManagedSite,
  createProjectForUser,
  deleteProjectForUser,
  addBomItem,
  addConfigArtifact,
  getDesignDetails,
  getProjectForUser,
  getSectorReviewStatus,
  getChangePlanApprovalReadiness,
  requestChangePlanApproval,
  approveChangePlan,
  listChangePlans,
  listDiscoveryRuns,
  listBomItems,
  listConfigArtifacts,
  listAuditEventsForUser,
  listManagedDevices,
  listManagedSites,
  listProjectsForUser,
  recordDeviceObservation,
  recordVirtualTest,
  registerManagedDevice,
  requestDeploymentApproval,
  transitionDiscoveryRun,
  saveDesignDetails,
  updateProjectSector,
  updateProjectQuestionnaire,
} from "./autonet";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { adminProcedure, protectedProcedure, publicProcedure, router } from "./_core/trpc";
import { COOKIE_NAME } from "../shared/const";
import { VENDOR_SUPPORT_STATUS } from "../shared/vendorSupport";
import { assessRecommendation, assessRestrictedClaim } from "./automationPolicy";
import { assessBenchmarkCoverage } from "./benchmarkPolicy";

const projectIdInput = z.object({ projectId: z.number().int().positive() });

function actorFromUser(user: { id: number; name?: string | null; email?: string | null }) {
  return { id: user.id, name: user.name, email: user.email };
}

function projectNotFound(): never {
  throw new TRPCError({ code: "NOT_FOUND", message: "Project not found." });
}

export const appRouter = router({
  system: systemRouter,
  claims: router({
    assessPublication: protectedProcedure
      .input(z.object({
        claimClass: z.enum(["engineer_equivalence", "production_safe", "compatibility", "compliance"]),
        scopeDescription: z.string().trim().max(1000),
        authorityReference: z.string().trim().max(1000),
        measuredEvidenceReference: z.string().trim().max(1000),
        reviewedAt: z.coerce.date().nullable(),
        benchmarkScenario: z.object({
          scenarioId: z.string().trim().max(200),
          vendorFamily: z.enum(["cisco", "huawei", "fortinet", "hpe_aruba"]),
          platform: z.string().trim().max(160),
          softwareVersion: z.string().trim().max(160),
          licenseEvidenceReference: z.string().trim().max(1000),
          configurationPathReference: z.string().trim().max(1000),
          sectorProfile: z.enum(["enterprise", "financial_service_branch", "retail_transaction_branch", "industrial"]),
          measuredRuns: z.number().int().nonnegative(),
          acceptedRuns: z.number().int().nonnegative(),
          rejectedRuns: z.number().int().nonnegative(),
          evidenceReference: z.string().trim().max(1000),
          reviewedAt: z.coerce.date().nullable(),
        }),
      }))
      .mutation(({ input }) => {
        const claimAssessment = assessRestrictedClaim(input);
        const coverage = assessBenchmarkCoverage(input.benchmarkScenario);
        if (claimAssessment.status === "blocked") return claimAssessment;
        return coverage.status === "measured_coverage"
          ? claimAssessment
          : { status: "blocked" as const, missing: coverage.blockers };
      }),
  }),
  recommendations: router({
    assess: protectedProcedure
      .input(z.object({
        sourceFacts: z.array(z.string().trim().min(1).max(500)).max(100),
        rationale: z.string().trim().max(2000),
        alternatives: z.array(z.string().trim().min(1).max(500)).max(20),
        affectedDevices: z.array(z.string().trim().min(1).max(200)).max(100),
        unresolvedItems: z.array(z.string().trim().min(1).max(500)).max(100),
        requiredAuthority: z.enum(["reviewer", "approver", "executor", "emergency_authorizer"]).nullable(),
      }))
      .mutation(({ input }) => assessRecommendation(input)),
  }),
  vendorSupport: router({
    list: protectedProcedure.query(() => VENDOR_SUPPORT_STATUS),
  }),
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return { success: true } as const;
    }),
  }),
  projects: router({
    list: protectedProcedure.query(({ ctx }) => listProjectsForUser(ctx.user.id)),
    get: protectedProcedure.input(projectIdInput).query(async ({ ctx, input }) => {
      const project = await getProjectForUser(input.projectId, ctx.user.id);
      return project || projectNotFound();
    }),
    create: protectedProcedure
      .input(
        z.object({
          name: z.string().trim().min(2).max(160),
          organization: z.string().trim().max(160).optional(),
        }),
      )
      .mutation(({ ctx, input }) => createProjectForUser(input, actorFromUser(ctx.user))),
    remove: protectedProcedure.input(projectIdInput).mutation(async ({ ctx, input }) => {
      const deleted = await deleteProjectForUser(input.projectId, actorFromUser(ctx.user));
      if (!deleted) {
        projectNotFound();
      }
      return { deleted: true } as const;
    }),
    updateQuestionnaire: protectedProcedure
      .input(
        z.object({
          projectId: z.number().int().positive(),
          organization: z.string().trim().max(160),
          organizationType: z.string().trim().max(120),
          siteCount: z.number().int().min(0).max(100000),
          classification: z.enum(["greenfield", "brownfield", "undetermined"]),
          vendorPreferences: z.string().trim().max(1000),
          complianceNeeds: z.string().trim().max(1000),
        }),
      )
      .mutation(async ({ ctx, input }) => {
        const project = await updateProjectQuestionnaire(input.projectId, input, actorFromUser(ctx.user));
        return project || projectNotFound();
      }),
    sectorReview: protectedProcedure.input(projectIdInput).query(async ({ ctx, input }) => {
      const status = await getSectorReviewStatus(input.projectId, ctx.user.id);
      if (status === undefined) projectNotFound();
      return status;
    }),
    updateSector: protectedProcedure
      .input(z.object({
        projectId: z.number().int().positive(),
        sectorProfile: z.enum(["enterprise", "financial_service_branch", "retail_transaction_branch", "industrial"]),
        suppliedInputs: z.array(z.string().trim().min(1).max(500)).max(20),
      }))
      .mutation(async ({ ctx, input }) => {
        const project = await updateProjectSector(input.projectId, input, actorFromUser(ctx.user));
        return project || projectNotFound();
      }),
    design: router({
      get: protectedProcedure.input(projectIdInput).query(async ({ ctx, input }) => {
        const details = await getDesignDetails(input.projectId, ctx.user.id);
        if (details === undefined) projectNotFound();
        return details;
      }),
      save: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          topologySummary: z.string().trim().max(2000),
          vlanPlan: z.string().trim().max(2000),
          ipAddressingSummary: z.string().trim().max(2000),
          decisionRecords: z.string().trim().max(8000),
        }))
        .mutation(async ({ ctx, input }) => {
          const details = await saveDesignDetails(input.projectId, input, actorFromUser(ctx.user));
          if (details === undefined) projectNotFound();
          return details;
        }),
    }),
    bom: router({
      list: protectedProcedure.input(projectIdInput).query(async ({ ctx, input }) => {
        const items = await listBomItems(input.projectId, ctx.user.id);
        if (items === undefined) projectNotFound();
        return items;
      }),
      add: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          category: z.enum(["device", "optic", "license", "support", "labor", "rack", "cable", "spare"]),
          description: z.string().trim().min(2).max(500),
          quantity: z.number().int().positive().max(100000),
          costEstimate: z.string().trim().max(120),
        }))
        .mutation(async ({ ctx, input }) => {
          const items = await addBomItem(input.projectId, input, actorFromUser(ctx.user));
          if (items === undefined) projectNotFound();
          return items;
        }),
    }),
    configs: router({
      list: protectedProcedure.input(projectIdInput).query(async ({ ctx, input }) => {
        const artifacts = await listConfigArtifacts(input.projectId, ctx.user.id);
        if (artifacts === undefined) projectNotFound();
        return artifacts;
      }),
      add: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          vendor: z.string().trim().min(2).max(120),
          deviceName: z.string().trim().min(2).max(160),
          artifactSummary: z.string().trim().max(2000),
          artifactPreview: z.string().trim().max(8000),
          featureGuard: z.enum(["pass", "blocked", "unknown"]),
          unsupportedFeatureLog: z.string().trim().max(2000),
        }))
        .mutation(async ({ ctx, input }) => {
          const artifacts = await addConfigArtifact(input.projectId, input, actorFromUser(ctx.user));
          if (artifacts === undefined) projectNotFound();
          return artifacts;
      }),
    }),
    discoveryRuns: router({
      list: protectedProcedure.input(projectIdInput).query(async ({ ctx, input }) => {
        const runs = await listDiscoveryRuns(input.projectId, ctx.user.id);
        if (runs === undefined) projectNotFound();
        return runs;
      }),
      create: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          siteId: z.number().int().positive(),
          scopeHash: z.string().trim().min(8).max(160),
          evidenceSummary: z.string().trim().max(4000).optional(),
          evidenceHash: z.string().trim().max(160).optional(),
          ambiguousCount: z.number().int().min(0).max(100000).optional(),
          unsupportedCount: z.number().int().min(0).max(100000).optional(),
        }))
        .mutation(async ({ ctx, input }) => {
          const run = await createDiscoveryRun(input.projectId, input, actorFromUser(ctx.user));
          if (run === undefined) projectNotFound();
          return run;
        }),
      transition: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          runId: z.number().int().positive(),
          nextState: z.enum(["queued", "running", "completed", "partial", "failed", "blocked"]),
          evidenceSummary: z.string().trim().max(4000).optional(),
          evidenceHash: z.string().trim().max(160).optional(),
          ambiguousCount: z.number().int().min(0).max(100000).optional(),
          unsupportedCount: z.number().int().min(0).max(100000).optional(),
        }))
        .mutation(async ({ ctx, input }) => {
          const run = await transitionDiscoveryRun(input.runId, input.nextState, input, actorFromUser(ctx.user));
          if (run === undefined) projectNotFound();
          return run;
        }),
    }),
    sites: router({
      list: protectedProcedure.input(projectIdInput).query(async ({ ctx, input }) => {
        const sites = await listManagedSites(input.projectId, ctx.user.id);
        if (sites === undefined) projectNotFound();
        return sites;
      }),
      create: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          name: z.string().trim().min(2).max(160),
          approvedScopeReference: z.string().trim().min(2).max(200),
        }))
        .mutation(async ({ ctx, input }) => {
          const sites = await createManagedSite(input.projectId, input, actorFromUser(ctx.user));
          if (sites === undefined) projectNotFound();
          return sites;
        }),
    }),
    devices: router({
      list: protectedProcedure.input(projectIdInput).query(async ({ ctx, input }) => {
        const devices = await listManagedDevices(input.projectId, ctx.user.id);
        if (devices === undefined) projectNotFound();
        return devices;
      }),
      register: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          siteId: z.number().int().positive(),
          deviceReference: z.string().trim().min(2).max(200),
          managementAddress: z.string().trim().min(2).max(255),
          protocol: z.enum(["ssh", "netconf", "https_api", "snmp"]),
          credentialReference: z.string().trim().min(2).max(160),
        }))
        .mutation(async ({ ctx, input }) => {
          const devices = await registerManagedDevice(input.projectId, input, actorFromUser(ctx.user));
          if (devices === undefined) projectNotFound();
          return devices;
        }),
      recordObservation: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          deviceId: z.number().int().positive(),
          observedVendor: z.string().trim().max(120),
          observedPlatform: z.string().trim().max(160),
          observedVersion: z.string().trim().max(160),
          factsHash: z.string().trim().max(160),
          factState: z.enum(["observed", "ambiguous", "unreachable", "unsupported"]),
          capabilityVerified: z.boolean(),
        }))
        .mutation(async ({ ctx, input }) => {
          const device = await recordDeviceObservation(input.projectId, input.deviceId, input, actorFromUser(ctx.user));
          if (device === undefined) projectNotFound();
          return device;
        }),
    }),
    changePlans: router({
      list: protectedProcedure.input(projectIdInput).query(async ({ ctx, input }) => {
        const plans = await listChangePlans(input.projectId, ctx.user.id);
        if (plans === undefined) projectNotFound();
        return plans;
      }),
      create: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          deviceId: z.number().int().positive(),
          name: z.string().trim().min(2).max(200),
          artifactHash: z.string().trim().min(8).max(160),
          scopeHash: z.string().trim().min(8).max(160),
        }))
        .mutation(async ({ ctx, input }) => {
          const plans = await createChangePlan(input.projectId, input, actorFromUser(ctx.user));
          if (plans === undefined) projectNotFound();
          return plans;
        }),
      approvalReadiness: protectedProcedure.input(z.object({ changePlanId: z.number().int().positive() })).query(async ({ ctx, input }) => {
        const readiness = await getChangePlanApprovalReadiness(input.changePlanId, ctx.user.id);
        if (readiness === undefined) projectNotFound();
        return readiness;
      }),
      requestApproval: protectedProcedure.input(z.object({ changePlanId: z.number().int().positive() })).mutation(async ({ ctx, input }) => {
        const readiness = await requestChangePlanApproval(input.changePlanId, actorFromUser(ctx.user));
        if (readiness === undefined) projectNotFound();
        return readiness;
      }),
      approve: adminProcedure.input(z.object({ changePlanId: z.number().int().positive() })).mutation(async ({ ctx, input }) => {
        const result = await approveChangePlan(input.changePlanId, actorFromUser(ctx.user));
        if (result === undefined) projectNotFound();
        return result;
      }),
      recordVirtualTest: protectedProcedure
        .input(z.object({
          projectId: z.number().int().positive(),
          changePlanId: z.number().int().positive(),
          state: z.enum(["not_tested", "test_queued", "test_passed", "test_failed", "test_inconclusive", "not_supported_for_virtual_test"]),
          adapterKind: z.string().trim().min(2).max(120),
          fidelityLabel: z.string().trim().min(2).max(120),
          artifactHash: z.string().trim().min(8).max(160),
          targetFactsHash: z.string().trim().min(8).max(160),
          scopeHash: z.string().trim().min(8).max(160),
          detail: z.string().trim().max(1000),
        }))
        .mutation(async ({ ctx, input }) => {
          const plan = await recordVirtualTest(input.projectId, input.changePlanId, input, actorFromUser(ctx.user));
          if (plan === undefined) projectNotFound();
          return plan;
        }),
    }),
    requestApproval: protectedProcedure.input(projectIdInput).mutation(async ({ ctx, input }) => {
      const project = await requestDeploymentApproval(input.projectId, actorFromUser(ctx.user));
      return project || projectNotFound();
    }),
    approve: adminProcedure.input(projectIdInput).mutation(async ({ ctx, input }) => {
      const projectId = await approveDeployment(input.projectId, actorFromUser(ctx.user));
      if (!projectId) {
        projectNotFound();
      }
      return { approved: true } as const;
    }),
  }),
  audit: router({
    list: protectedProcedure
      .input(z.object({ page: z.number().int().positive().default(1), pageSize: z.number().int().min(1).max(50).default(10) }))
      .query(({ ctx, input }) => listAuditEventsForUser(ctx.user.id, input.page, input.pageSize)),
  }),
});

export type AppRouter = typeof appRouter;
