import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export const networkProjects = mysqlTable("network_projects", {
  id: int("id").autoincrement().primaryKey(),
  ownerId: int("owner_id").notNull(),
  name: varchar("name", { length: 160 }).notNull(),
  organization: varchar("organization", { length: 160 }).notNull().default(""),
  organizationType: varchar("organization_type", { length: 120 }).notNull().default(""),
  siteCount: int("site_count").notNull().default(0),
  classification: mysqlEnum("classification", ["greenfield", "brownfield", "undetermined"])
    .notNull()
    .default("undetermined"),
  vendorPreferences: varchar("vendor_preferences", { length: 1000 }).notNull().default(""),
  complianceNeeds: varchar("compliance_needs", { length: 1000 }).notNull().default(""),
  status: mysqlEnum("status", ["intake", "design", "ready_for_review", "approved"])
    .notNull()
    .default("intake"),
  questionnaireComplete: int("questionnaire_complete").notNull().default(0),
  requirementsComplete: int("requirements_complete").notNull().default(0),
  approvalState: mysqlEnum("approval_state", ["not_requested", "pending", "approved", "blocked"])
    .notNull()
    .default("not_requested"),
  approvedBy: varchar("approved_by", { length: 160 }),
  approvedAt: timestamp("approved_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export const auditEvents = mysqlTable("audit_events", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull(),
  actorId: int("actor_id").notNull(),
  actorName: varchar("actor_name", { length: 160 }).notNull(),
  action: varchar("action", { length: 100 }).notNull(),
  details: text("details").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const projectDesignDetails = mysqlTable("project_design_details", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull().unique(),
  topologySummary: varchar("topology_summary", { length: 2000 }).notNull().default(""),
  vlanPlan: varchar("vlan_plan", { length: 2000 }).notNull().default(""),
  ipAddressingSummary: varchar("ip_addressing_summary", { length: 2000 }).notNull().default(""),
  decisionRecords: varchar("decision_records", { length: 8000 }).notNull().default(""),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export const projectBomItems = mysqlTable("project_bom_items", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull(),
  category: mysqlEnum("category", ["device", "optic", "license", "support", "labor", "rack", "cable", "spare"])
    .notNull(),
  description: varchar("description", { length: 500 }).notNull(),
  quantity: int("quantity").notNull(),
  costEstimate: varchar("cost_estimate", { length: 120 }).notNull().default(""),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const projectConfigArtifacts = mysqlTable("project_config_artifacts", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull(),
  vendor: varchar("vendor", { length: 120 }).notNull(),
  deviceName: varchar("device_name", { length: 160 }).notNull(),
  artifactSummary: varchar("artifact_summary", { length: 2000 }).notNull().default(""),
  artifactPreview: varchar("artifact_preview", { length: 8000 }).notNull().default(""),
  featureGuard: mysqlEnum("feature_guard", ["pass", "blocked", "unknown"]).notNull().default("unknown"),
  unsupportedFeatureLog: varchar("unsupported_feature_log", { length: 2000 }).notNull().default(""),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;
export type NetworkProject = typeof networkProjects.$inferSelect;
export type InsertNetworkProject = typeof networkProjects.$inferInsert;
export type AuditEvent = typeof auditEvents.$inferSelect;
export type ProjectDesignDetail = typeof projectDesignDetails.$inferSelect;
export type InsertProjectDesignDetail = typeof projectDesignDetails.$inferInsert;
export type ProjectBomItem = typeof projectBomItems.$inferSelect;
export type InsertProjectBomItem = typeof projectBomItems.$inferInsert;
export type ProjectConfigArtifact = typeof projectConfigArtifacts.$inferSelect;
export type InsertProjectConfigArtifact = typeof projectConfigArtifacts.$inferInsert;
