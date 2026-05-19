export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type Finding = {
  id: string;
  module: string;
  severity: Severity;
  title: string;
  description: string;
  affected_line?: number | null;
  affected_function?: string | null;
  affected_code?: string | null;
  confidence: "high" | "medium" | "low";
  source: string;
  category?: string;
  rule_id?: string | null;
  fingerprint?: string | null;
  business_impact: string;
  developer_explanation: string;
  recommendation: string;
  references?: string[];
  paid_review_recommended: boolean;
  ai_explanation?: Record<string, unknown> | null;
};

export type ScanResponse = {
  report_id: string;
  generated_at: string;
  project_name?: string | null;
  module_score: {
    module: string;
    score: number;
    risk_label: string;
    assessed: boolean;
  };
  findings: Finding[];
  severity_breakdown?: Record<Severity, number>;
  priority_actions?: string[];
  input_hash?: string | null;
  engine_version?: string;
  scan_metadata?: Record<string, unknown>;
  disclaimer: string;
};

export type AIExplanation = {
  status: "disabled" | "fallback" | "provider_success" | "provider_error" | "blocked_by_policy";
  provider: string;
  mode: string;
  language: string;
  summary: string;
  business_impact: string;
  developer_guidance: string;
  safe_fix_direction: string;
  manual_review_note: string;
  confidence_note: string;
  safety_note: string;
};

export type CombinedLaunchReport = {
  report_id: string;
  generated_at: string;
  project_name: string;
  report_mode: string;
  language: string;
  scores: Record<string, number>;
  report_hash: string;
  combined: {
    overall_score?: number | null;
    available_score?: number | null;
    risk_label: string;
    assessed_modules?: string[];
    missing_modules?: string[];
  };
  coverage: {
    assessed_count: number;
    total_modules: number;
    coverage_percent: number;
    assessed_modules: string[];
    missing_modules: string[];
    confidence: string;
    note: string;
  };
  score_confidence: string;
  severity_breakdown: Record<Severity, number>;
  module_summaries: Array<{
    module: string;
    label?: string;
    score: number;
    risk_label: string;
    findings_count: number;
    critical_high_count: number;
    report_id: string;
    engine_version?: string;
    assessed?: boolean;
  }>;
  module_matrix: Array<{
    module: string;
    label: string;
    weight_percent: number;
    assessed: boolean;
    score?: number | null;
    risk_label: string;
    findings_count?: number | null;
    critical_high_count?: number | null;
    status: string;
    evidence: string;
  }>;
  executive_summary: string;
  risk_narrative: string;
  priority_action_plan: Array<{
    step: number;
    severity: Severity;
    title: string;
    module: string;
    module_label?: string;
    recommended_action: string;
    business_impact?: string;
    manual_review_recommended: boolean;
  }>;
  top_findings: Finding[];
  package_recommendation: {
    package_id?: string;
    package: string;
    reason: string;
    cta?: string;
  };
  before_launch_checklist: string[];
  limitations: string[];
  next_steps: string[];
  public_summary_note: string;
  client_delivery: {
    report_id: string;
    verification_hash: string;
    delivery_formats: string[];
    recommended_cta: string;
    public_wording: string;
    do_not_use_wording: string[];
    manual_verification_required: boolean;
  };
  ai_status: {
    ai_enabled: boolean;
    provider: string;
    provider_configured: boolean;
    ai_send_code: boolean;
    mode: string;
    disclaimer: string;
  };
  ai_summary?: AIExplanation | null;
  disclaimer: string;
  markdown_report: string;
  json_export?: Record<string, unknown>;
};

export type BillingCycle = "one_time" | "monthly" | "annual";
export type PaymentProvider = "upi_manual" | "razorpay";
export type PaymentStatus = "created" | "pending" | "reference_submitted" | "manual_verification_pending" | "verified" | "failed" | "cancelled" | "razorpay_order_created" | "razorpay_payment_authorized" | "razorpay_paid" | "webhook_verified" | "refunded" | "expired";

export type PackagePlan = {
  id: string;
  name: string;
  category?: "free" | "service" | "subscription";
  price_inr: number;
  billing_cycles?: BillingCycle[];
  description: string;
  deliverables: string[];
  turnaround_time: string;
  cta: string;
  upi_payment?: {
    enabled: boolean;
    upi_id: string;
    upi_name: string;
    deep_link: string | null;
    note: string;
    manual_verification_required?: boolean;
  };
  popular?: boolean;
};

export type PaymentIntent = {
  id: string;
  created_at: string;
  package_id: string;
  package_name: string;
  amount_inr: number;
  amount_paise?: number;
  currency?: string;
  billing_cycle: BillingCycle;
  customer_name?: string | null;
  customer_email?: string | null;
  project_name?: string | null;
  user_id?: string | null;
  organization_id?: string | null;
  provider?: PaymentProvider;
  provider_preference?: "auto" | "razorpay" | "upi_manual";
  upi_id: string;
  upi_name: string;
  upi_deep_link?: string | null;
  manual_verification_required: boolean;
  razorpay_enabled?: boolean;
  razorpay_key_id?: string | null;
  razorpay_order_id?: string | null;
  razorpay_payment_id?: string | null;
  razorpay_signature?: string | null;
  razorpay_receipt?: string | null;
  razorpay_order_status?: string | null;
  razorpay_checkout_options?: Record<string, unknown>;
  verified_at?: string | null;
  webhook_verified_at?: string | null;
  subscription_id?: string | null;
  status: PaymentStatus | string;
  note: string;
};

export type PaymentGatewayStatus = {
  ok: boolean;
  phase: string;
  payment_mode: string;
  upi_manual_enabled: boolean;
  upi_id_configured: boolean;
  razorpay_enabled: boolean;
  razorpay_configured: boolean;
  razorpay_key_id_public?: string | null;
  razorpay_webhook_configured: boolean;
  auto_payment_verification: boolean;
  manual_verification_fallback: boolean;
  real_only_note: string;
  blocked_claims: string[];
};

export type SubscriptionRecord = {
  id: string;
  created_at: string;
  package_id: string;
  plan_name: string;
  billing_cycle: BillingCycle;
  amount_inr: number;
  currency: string;
  status: string;
  customer_name?: string | null;
  customer_email?: string | null;
  user_id?: string | null;
  organization_id?: string | null;
  payment_intent_id?: string | null;
  provider?: PaymentProvider;
  current_period_start?: string | null;
  current_period_end?: string | null;
  activated_at?: string | null;
  cancelled_at?: string | null;
  manual_verification_required: boolean;
  notes?: string[];
};

export type UnifiedModuleCard = {
  module: string;
  label: string;
  status: string;
  score?: number | null;
  risk_label: string;
  assessed: boolean;
  report_id?: string | null;
  findings_count: number;
  critical_high_count: number;
  evidence: string[];
  limitations: string[];
  required_input: string[];
};

export type UnifiedScoreSplitItem = {
  label: string;
  score?: number | null;
  status: string;
  risk_label?: string;
  source: string;
};

export type UnifiedScoreSplit = {
  website_surface_score?: UnifiedScoreSplitItem;
  contract_rule_score?: UnifiedScoreSplitItem;
  launch_evidence_score?: UnifiedScoreSplitItem;
  overall_launch_confidence?: UnifiedScoreSplitItem;
  no_full_audit_score?: boolean;
  note?: string;
  [key: string]: UnifiedScoreSplitItem | boolean | string | undefined;
};

export type UnifiedUrlScanResponse = {
  report_id: string;
  generated_at: string;
  project_name?: string | null;
  engine_version: string;
  mode: string;
  website_url: string;
  chain?: string | null;
  project_type?: string | null;
  realness_rule: string;
  available_score?: number | null;
  overall_score?: number | null;
  risk_label?: string | null;
  score_split?: UnifiedScoreSplit;
  coverage?: CombinedLaunchReport["coverage"];
  assessed_modules: string[];
  not_assessed_modules: string[];
  live_module_count: number;
  module_cards: UnifiedModuleCard[];
  surface_hints: Record<string, unknown>;
  priority_actions: CombinedLaunchReport["priority_action_plan"];
  combined_report: CombinedLaunchReport;
  feature_status_matrix: Array<Record<string, string>>;
  warnings: string[];
  safe_public_summary: string;
  blocked_claims: string[];
  next_real_inputs_needed: string[];
  disclaimer: string;
};

export type ProjectRecord = {
  id: string;
  user_id: string;
  name: string;
  website_url?: string | null;
  chain?: string | null;
  contract_address?: string | null;
  github_repo_url?: string | null;
  project_type?: string | null;
  description?: string | null;
  owner_contact?: string | null;
  created_at: string;
  updated_at?: string | null;
};

export type ScanHistoryRecord = {
  id: string;
  user_id: string;
  project_id?: string | null;
  module: string;
  project_name?: string | null;
  score?: number | null;
  risk_label?: string | null;
  report_id?: string | null;
  input_hash?: string | null;
  findings_count: number;
  critical_high_count: number;
  status?: string;
  notes?: string | null;
  payload?: Record<string, unknown>;
  created_at: string;
};

export type SavedReportRecord = {
  id: string;
  user_id: string;
  project_id?: string | null;
  scan_id?: string | null;
  report_id: string;
  title: string;
  report_hash?: string | null;
  overall_score?: number | null;
  available_score?: number | null;
  risk_label?: string | null;
  visibility?: string;
  status?: string;
  payload?: Record<string, unknown>;
  created_at: string;
};

export type DashboardActivityItem = {
  id: string;
  type: "project" | "scan" | "report";
  title: string;
  subtitle?: string | null;
  created_at: string;
  project_id?: string | null;
  href?: string | null;
};

export type ProjectDetail = {
  project: ProjectRecord;
  scans: ScanHistoryRecord[];
  reports: SavedReportRecord[];
  activity: DashboardActivityItem[];
  totals: Record<string, number | string | null>;
};

export type WorkspaceRole = "owner" | "admin" | "reviewer" | "member" | "viewer";
export type MemberStatus = "active" | "invited" | "removed";
export type FindingTaskStatus = "open" | "in_progress" | "fixed" | "false_positive" | "accepted_risk" | "needs_manual_review";

export type OrganizationRecord = {
  id: string;
  owner_user_id: string;
  name: string;
  website_url?: string | null;
  billing_email?: string | null;
  gst_number?: string | null;
  notes?: string | null;
  plan: string;
  created_at: string;
  updated_at?: string | null;
};

export type OrganizationMemberRecord = {
  id: string;
  organization_id: string;
  user_id?: string | null;
  email?: string | null;
  full_name?: string | null;
  role: WorkspaceRole;
  status: MemberStatus;
  invited_by_user_id?: string | null;
  created_at: string;
  updated_at?: string | null;
  note?: string | null;
};

export type FindingTaskRecord = {
  id: string;
  organization_id: string;
  project_id?: string | null;
  scan_id?: string | null;
  report_id?: string | null;
  finding_id?: string | null;
  title: string;
  module: string;
  severity: Severity;
  status: FindingTaskStatus;
  assigned_to_member_id?: string | null;
  assigned_to_user_id?: string | null;
  due_date?: string | null;
  recommendation?: string | null;
  evidence?: Record<string, unknown>;
  created_by_user_id: string;
  created_at: string;
  updated_at?: string | null;
};

export type WorkspaceCommentRecord = {
  id: string;
  organization_id: string;
  project_id?: string | null;
  scan_id?: string | null;
  report_id?: string | null;
  finding_task_id?: string | null;
  body: string;
  created_by_user_id: string;
  created_at: string;
};

export type WorkspaceActivityRecord = {
  id: string;
  organization_id: string;
  type: "organization" | "member" | "project" | "scan" | "report" | "task" | "comment";
  title: string;
  subtitle?: string | null;
  created_by_user_id?: string | null;
  created_at: string;
  target_id?: string | null;
};

export type WorkspaceOverview = {
  organization: OrganizationRecord;
  current_user_role?: WorkspaceRole | null;
  members: OrganizationMemberRecord[];
  projects: ProjectRecord[];
  scans: ScanHistoryRecord[];
  reports: SavedReportRecord[];
  finding_tasks: FindingTaskRecord[];
  comments: WorkspaceCommentRecord[];
  activity: WorkspaceActivityRecord[];
  totals: Record<string, number | string | null>;
  real_only_note: string;
};

export type SecureScoreFinding = {
  id: string;
  scan_id: string;
  project_id?: string | null;
  report_id?: string | null;
  module: string;
  module_label?: string;
  severity: Severity;
  title: string;
  description: string;
  affected_line?: number | null;
  affected_function?: string | null;
  confidence?: string;
  source?: string;
  category?: string;
  business_impact?: string;
  recommendation?: string;
  paid_review_recommended?: boolean;
  created_at?: string;
  project_name?: string | null;
  risk_label?: string | null;
  workflow_key?: string;
  workflow_status: "open" | "in_progress" | "fixed" | "false_positive" | "accepted_risk" | "needs_manual_review";
  workflow_notes?: string | null;
  assigned_to?: string | null;
  updated_at?: string | null;
  is_open?: boolean;
};

export type SecureScoreOverview = {
  user_id: string;
  summary: {
    projects: number;
    saved_scans: number;
    findings: number;
    open_findings: number;
    open_critical_high: number;
    average_score?: number | null;
    risk_label: string;
  };
  severity_breakdown: Record<string, number>;
  workflow_breakdown: Record<string, number>;
  module_findings: Record<string, number>;
  risk_buckets: Record<string, number>;
  module_scorecards: Array<{
    module: string;
    label: string;
    average_score?: number | null;
    latest_score?: number | null;
    risk_label: string;
    scans_count: number;
    findings_count: number;
    critical_high_count: number;
    latest_scan_id: string;
  }>;
  score_trend: Array<{ scan_id: string; created_at: string; module: string; score?: number | null; risk_label: string }>;
  top_open_findings: SecureScoreFinding[];
  real_only_note: string;
  auto_fix_status: string;
};

export type AIFixAssistantStatus = {
  ok: boolean;
  phase: string;
  ai_enabled: boolean;
  ai_fix_enabled: boolean;
  provider: string;
  model: string;
  provider_configured: boolean;
  mode: "provider" | "safe_fallback" | string;
  ai_send_code: boolean;
  ai_fix_send_code: boolean;
  max_code_chars: number;
  auto_apply_allowed: boolean;
  code_will_be_sent_only_if: string[];
  blocked_claims: string[];
  real_only_note: string;
};

export type AIFixSuggestion = {
  status: string;
  provider: string;
  model: string;
  generated_at: string;
  language: string;
  finding_id: string;
  finding_title: string;
  finding_severity: Severity;
  summary: string;
  root_cause: string;
  safe_patch_strategy: string;
  suggested_patch_unified_diff: string;
  fixed_code_snippet: string;
  test_suggestions: string[];
  validation_steps: string[];
  risk_notes: string[];
  manual_review_note: string;
  confidence_note: string;
  auto_apply_allowed: boolean;
  code_was_sent_to_provider: boolean;
  redaction_applied: boolean;
  safety_flags: string[];
  safety_note: string;
};

export type DashboardWorkflowTimelineItem = {
  id: string;
  type: "project" | "scan" | "report" | string;
  title: string;
  subtitle?: string | null;
  created_at: string;
  project_id?: string | null;
  href?: string | null;
};

export type DashboardWorkflowTrendPoint = {
  scan_id: string;
  created_at: string;
  module: string;
  score?: number | null;
  bucket: string;
  risk_label: string;
  findings_count: number;
  critical_high_count: number;
  href: string;
};

export type DashboardWorkflowModuleComparison = {
  module: string;
  scans_count: number;
  latest_scan_id: string;
  latest_score?: number | null;
  average_score?: number | null;
  latest_risk_label: string;
  findings_count: number;
  critical_high_count: number;
  last_seen_at: string;
  href: string;
};

export type DashboardWorkflowProjectHealth = {
  project_id?: string | null;
  name: string;
  website_url?: string | null;
  chain?: string | null;
  scans_count: number;
  reports_count: number;
  average_score?: number | null;
  critical_high_count: number;
  latest_scan_at?: string | null;
  latest_risk_label?: string | null;
  href: string;
};

export type DashboardWorkflowFindingTask = {
  id: string;
  scan_id?: string | null;
  report_id?: string | null;
  project_id?: string | null;
  module: string;
  title: string;
  severity: Severity | string;
  status: string;
  recommendation?: string | null;
  created_at: string;
  href: string;
};

export type DashboardWorkflow = {
  ok: boolean;
  scope: {
    mode: "workspace" | "project" | string;
    project_id?: string | null;
    project_name?: string | null;
  };
  summary: Record<string, number | string | null>;
  timeline: DashboardWorkflowTimelineItem[];
  risk_trend: DashboardWorkflowTrendPoint[];
  module_comparison: DashboardWorkflowModuleComparison[];
  project_health: DashboardWorkflowProjectHealth[];
  finding_workflow: {
    tasks: DashboardWorkflowFindingTask[];
    status_breakdown: Record<string, number>;
    severity_breakdown: Record<string, number>;
    note: string;
  };
  real_only_note: string;
  storage_note: string;
};
