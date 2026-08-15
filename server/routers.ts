import { TRPCError } from "@trpc/server";
import { z } from "zod";
import {
  approveDeployment,
  createProjectForUser,
  deleteProjectForUser,
  addBomItem,
  addConfigArtifact,
  getDesignDetails,
  getProjectForUser,
  listBomItems,
  listConfigArtifacts,
  listAuditEventsForUser,
  listProjectsForUser,
  requestDeploymentApproval,
  saveDesignDetails,
  updateProjectQuestionnaire,
} from "./autonet";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { adminProcedure, protectedProcedure, publicProcedure, router } from "./_core/trpc";
import { COOKIE_NAME } from "../shared/const";

const projectIdInput = z.object({ projectId: z.number().int().positive() });

function actorFromUser(user: { id: number; name?: string | null; email?: string | null }) {
  return { id: user.id, name: user.name, email: user.email };
}

function projectNotFound(): never {
  throw new TRPCError({ code: "NOT_FOUND", message: "Project not found." });
}

export const appRouter = router({
  system: systemRouter,
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
