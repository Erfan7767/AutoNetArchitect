import type { Express } from "express";
import { z } from "zod";
import { ingestSignedSiteAgentHealth } from "./agentHealth";

const signedHealthSchema = z.object({
  enrollmentId: z.string().trim().min(16).max(160),
  agentId: z.string().trim().min(3).max(160),
  siteId: z.number().int().positive(),
  scopeHash: z.string().trim().min(8).max(160),
  healthy: z.boolean(),
  mode: z.literal("read_only"),
  detail: z.string().trim().min(1).max(500),
  observedAt: z.string().datetime({ offset: true }),
  signature: z.string().trim().min(16).max(4096),
});

/** Register the signed, secret-free agent-health endpoint. It cannot perform discovery or device actions. */
export function registerSiteAgentHealthRoute(app: Express) {
  app.post("/api/site-agent/health", async (req, res) => {
    const parsed = signedHealthSchema.safeParse(req.body);
    if (!parsed.success) {
      res.status(400).json({ accepted: false, reason: "Health report payload is invalid." });
      return;
    }
    try {
      const result = await ingestSignedSiteAgentHealth(parsed.data);
      res.status(result.accepted ? 202 : 403).json(result);
    } catch {
      res.status(503).json({ accepted: false, reason: "Health reporting is temporarily unavailable." });
    }
  });
}
