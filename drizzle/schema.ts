import { boolean, int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

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
  sectorProfile: mysqlEnum("sector_profile", ["unselected", "enterprise", "financial_service_branch", "retail_transaction_branch", "industrial"])
    .notNull()
    .default("unselected"),
  sectorInputs: varchar("sector_inputs", { length: 8000 }).notNull().default("[]"),
  sectorInputsUpdatedAt: timestamp("sector_inputs_updated_at"),
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
  deviceId: int("device_id").notNull().default(0),
  vendor: varchar("vendor", { length: 120 }).notNull(),
  deviceName: varchar("device_name", { length: 160 }).notNull(),
  artifactSummary: varchar("artifact_summary", { length: 2000 }).notNull().default(""),
  artifactPreview: varchar("artifact_preview", { length: 8000 }).notNull().default(""),
  featureGuard: mysqlEnum("feature_guard", ["pass", "blocked", "unknown"]).notNull().default("unknown"),
  unsupportedFeatureLog: varchar("unsupported_feature_log", { length: 2000 }).notNull().default(""),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const managedSites = mysqlTable("managed_sites", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull(),
  name: varchar("name", { length: 160 }).notNull(),
  agentReference: varchar("agent_reference", { length: 160 }).notNull().default(""),
  approvedScopeReference: varchar("approved_scope_reference", { length: 200 }).notNull(),
  mode: mysqlEnum("mode", ["read_only", "prepared_change"]).notNull().default("read_only"),
  enrollmentState: mysqlEnum("enrollment_state", ["not_enrolled", "pending", "active", "revoked"])
    .notNull()
    .default("not_enrolled"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export const managedDevices = mysqlTable("managed_devices", {
  id: int("id").autoincrement().primaryKey(),
  siteId: int("site_id").notNull(),
  deviceReference: varchar("device_reference", { length: 200 }).notNull(),
  managementAddress: varchar("management_address", { length: 255 }).notNull(),
  protocol: mysqlEnum("protocol", ["ssh", "netconf", "https_api", "snmp"]).notNull(),
  credentialReference: varchar("credential_reference", { length: 160 }).notNull(),
  observedVendor: varchar("observed_vendor", { length: 120 }).notNull().default(""),
  observedPlatform: varchar("observed_platform", { length: 160 }).notNull().default(""),
  observedVersion: varchar("observed_version", { length: 160 }).notNull().default(""),
  factState: mysqlEnum("fact_state", ["unobserved", "observed", "ambiguous", "unreachable", "unsupported"])
    .notNull()
    .default("unobserved"),
  factsHash: varchar("facts_hash", { length: 160 }).notNull().default(""),
  capabilityVerified: boolean("capability_verified").notNull().default(false),
  capabilityEvidenceReference: varchar("capability_evidence_reference", { length: 1000 }).notNull().default(""),
  licenseEvidenceReference: varchar("license_evidence_reference", { length: 1000 }).notNull().default(""),
  configurationPathEvidenceReference: varchar("configuration_path_evidence_reference", { length: 1000 }).notNull().default(""),
  lastObservedAt: timestamp("last_observed_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export const discoveryRuns = mysqlTable("discovery_runs", {
  id: int("id").autoincrement().primaryKey(),
  siteId: int("site_id").notNull(),
  mode: mysqlEnum("mode", ["read_only"]).notNull().default("read_only"),
  state: mysqlEnum("state", ["queued", "running", "completed", "partial", "failed", "blocked"])
    .notNull()
    .default("queued"),
  scopeHash: varchar("scope_hash", { length: 160 }).notNull(),
  evidenceSummary: varchar("evidence_summary", { length: 4000 }).notNull().default(""),
  evidenceHash: varchar("evidence_hash", { length: 160 }).notNull().default(""),
  ambiguousCount: int("ambiguous_count").notNull().default(0),
  unsupportedCount: int("unsupported_count").notNull().default(0),
  startedAt: timestamp("started_at"),
  completedAt: timestamp("completed_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export const changePlans = mysqlTable("change_plans", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull(),
  deviceId: int("device_id").notNull(),
  name: varchar("name", { length: 200 }).notNull(),
  artifactHash: varchar("artifact_hash", { length: 160 }).notNull(),
  targetFactsHash: varchar("target_facts_hash", { length: 160 }).notNull(),
  scopeHash: varchar("scope_hash", { length: 160 }).notNull(),
  virtualValidationState: mysqlEnum("virtual_validation_state", ["not_tested", "test_queued", "test_passed", "test_failed", "test_inconclusive", "not_supported_for_virtual_test"])
    .notNull()
    .default("not_tested"),
  releaseState: mysqlEnum("release_state", ["draft", "blocked", "ready_for_approval", "approved", "executed", "rolled_back"])
    .notNull()
    .default("draft"),
  backupVerified: boolean("backup_verified").notNull().default(false),
  maintenanceWindowValid: boolean("maintenance_window_valid").notNull().default(false),
  sectorProfileSnapshot: varchar("sector_profile_snapshot", { length: 8000 }).notNull().default("{}"),
  sectorInputsHash: varchar("sector_inputs_hash", { length: 160 }).notNull().default(""),
  sectorReviewState: mysqlEnum("sector_review_state", ["current", "stale", "missing"]).notNull().default("missing"),
  sectorReviewedAt: timestamp("sector_reviewed_at"),
  humanApprover: varchar("human_approver", { length: 160 }),
  approvedAt: timestamp("approved_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export const virtualTestRuns = mysqlTable("virtual_test_runs", {
  id: int("id").autoincrement().primaryKey(),
  changePlanId: int("change_plan_id").notNull(),
  state: mysqlEnum("state", ["not_tested", "test_queued", "test_passed", "test_failed", "test_inconclusive", "not_supported_for_virtual_test"])
    .notNull(),
  adapterKind: varchar("adapter_kind", { length: 120 }).notNull(),
  fidelityLabel: varchar("fidelity_label", { length: 120 }).notNull(),
  artifactHash: varchar("artifact_hash", { length: 160 }).notNull(),
  targetFactsHash: varchar("target_facts_hash", { length: 160 }).notNull(),
  scopeHash: varchar("scope_hash", { length: 160 }).notNull(),
  detail: varchar("detail", { length: 1000 }).notNull().default(""),
  observedAt: timestamp("observed_at").defaultNow().notNull(),
});

/** Observed post-change verification records; this table never implies an execution action. */
export const postChangeVerificationRuns = mysqlTable("post_change_verification_runs", {
  id: int("id").autoincrement().primaryKey(),
  changePlanId: int("change_plan_id").notNull(),
  state: mysqlEnum("state", ["passed", "failed", "warning", "not_verifiable"]).notNull(),
  verificationType: mysqlEnum("verification_type", [
    "command_verification",
    "connectivity_verification",
    "service_verification",
    "routing_verification",
    "monitoring_verification",
    "user_verification",
  ]).notNull(),
  expectedOutcome: varchar("expected_outcome", { length: 1000 }).notNull(),
  observedOutcome: varchar("observed_outcome", { length: 2000 }).notNull(),
  evidenceReference: varchar("evidence_reference", { length: 1000 }).notNull(),
  rollbackReviewRequired: boolean("rollback_review_required").notNull().default(false),
  recordedBy: varchar("recorded_by", { length: 160 }).notNull(),
  observedAt: timestamp("observed_at").defaultNow().notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

/** Scoped evidence assessments for restricted language; never a production-authorization record. */
export const projectRestrictedClaims = mysqlTable("project_restricted_claims", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull(),
  claimClass: mysqlEnum("claim_class", ["engineer_equivalence", "production_safe", "compatibility", "compliance"]).notNull(),
  scopeDescription: varchar("scope_description", { length: 1000 }).notNull(),
  authorityReference: varchar("authority_reference", { length: 1000 }).notNull(),
  measuredEvidenceReference: varchar("measured_evidence_reference", { length: 1000 }).notNull(),
  reviewedAt: timestamp("reviewed_at"),
  assessmentStatus: mysqlEnum("assessment_status", ["publishable", "blocked"]).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
});

export const benchmarkScenarios = mysqlTable("benchmark_scenarios", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("project_id").notNull(),
  scenarioId: varchar("scenario_id", { length: 200 }).notNull(),
  vendorFamily: mysqlEnum("vendor_family", ["cisco", "huawei", "fortinet", "hpe_aruba"]).notNull(),
  platform: varchar("platform", { length: 160 }).notNull(),
  softwareVersion: varchar("software_version", { length: 160 }).notNull(),
  licenseEvidenceReference: varchar("license_evidence_reference", { length: 1000 }).notNull(),
  configurationPathReference: varchar("configuration_path_reference", { length: 1000 }).notNull(),
  sectorProfile: mysqlEnum("sector_profile", ["enterprise", "financial_service_branch", "retail_transaction_branch", "industrial"]).notNull(),
  measuredRuns: int("measured_runs").notNull(),
  acceptedRuns: int("accepted_runs").notNull(),
  rejectedRuns: int("rejected_runs").notNull(),
  evidenceReference: varchar("evidence_reference", { length: 1000 }).notNull(),
  reviewedAt: timestamp("reviewed_at").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().onUpdateNow().notNull(),
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
export type ManagedSite = typeof managedSites.$inferSelect;
export type InsertManagedSite = typeof managedSites.$inferInsert;
export type ManagedDevice = typeof managedDevices.$inferSelect;
export type InsertManagedDevice = typeof managedDevices.$inferInsert;
export type DiscoveryRun = typeof discoveryRuns.$inferSelect;
export type InsertDiscoveryRun = typeof discoveryRuns.$inferInsert;
export type ChangePlan = typeof changePlans.$inferSelect;
export type InsertChangePlan = typeof changePlans.$inferInsert;
export type VirtualTestRun = typeof virtualTestRuns.$inferSelect;
export type InsertVirtualTestRun = typeof virtualTestRuns.$inferInsert;
export type PostChangeVerificationRun = typeof postChangeVerificationRuns.$inferSelect;
export type InsertPostChangeVerificationRun = typeof postChangeVerificationRuns.$inferInsert;
export type ProjectRestrictedClaim = typeof projectRestrictedClaims.$inferSelect;
export type InsertProjectRestrictedClaim = typeof projectRestrictedClaims.$inferInsert;
export type BenchmarkScenario = typeof benchmarkScenarios.$inferSelect;
export type InsertBenchmarkScenario = typeof benchmarkScenarios.$inferInsert;
