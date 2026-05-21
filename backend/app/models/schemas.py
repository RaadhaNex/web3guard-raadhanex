from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

Severity = Literal["critical", "high", "medium", "low", "info"]
ScanModule = Literal["contract", "website", "website_advanced", "dapp", "api", "api_deep", "wallet", "wallet_risk", "admin_opsec", "github", "static_analysis", "deep_analysis", "permission_map", "launch_transparency", "contract_diff", "upgrade_safety", "monitoring_lite", "threat_intel", "bug_bounty", "public_registry", "developer_api", "notifications", "compliance", "cross_chain"]
Confidence = Literal["high", "medium", "low"]
ExplanationMode = Literal["founder", "developer", "hinglish", "executive"]
AIProviderStatus = Literal["disabled", "fallback", "provider_success", "provider_error", "blocked_by_policy"]
LeadStatus = Literal["New", "Contacted", "Payment Pending", "Paid", "In Review", "Delivered", "Closed", "Refunded", "Rejected / Out of Scope"]
PaymentStatus = Literal["created", "pending", "reference_submitted", "manual_verification_pending", "verified", "failed", "cancelled", "razorpay_order_created", "razorpay_payment_authorized", "razorpay_paid", "webhook_verified", "refunded", "expired"]
PaymentProvider = Literal["upi_manual", "razorpay"]
PaymentProviderPreference = Literal["auto", "razorpay", "upi_manual"]
SubscriptionStatus = Literal["pending", "active", "past_due", "cancelled", "expired", "manual_review"]
BillingCycle = Literal["one_time", "monthly", "annual"]
OwnershipVerificationMethod = Literal["dns_txt", "well_known"]
VerificationStatus = Literal["pending", "verified", "failed", "expired"]



class Finding(BaseModel):
    id: str
    module: ScanModule
    severity: Severity
    title: str
    description: str
    affected_file: str | None = None
    affected_line: int | None = None
    affected_column: int | None = None
    end_line: int | None = None
    affected_function: str | None = None
    affected_code: str | None = None
    confidence: Confidence = "medium"
    source: str = "Rule Engine"
    category: str = "general"
    rule_id: str | None = None
    fingerprint: str | None = None
    business_impact: str
    developer_explanation: str
    recommendation: str
    references: list[str] = []
    paid_review_recommended: bool = False
    ai_explanation: dict | None = None


class ModuleScore(BaseModel):
    module: ScanModule
    score: int
    risk_label: str
    assessed: bool = True


class ScanResponse(BaseModel):
    report_id: str
    generated_at: datetime
    project_name: str | None = None
    module_score: ModuleScore
    findings: list[Finding]
    severity_breakdown: dict[str, int] = {}
    priority_actions: list[str] = []
    input_hash: str | None = None
    engine_version: str = "web3guard-rule-engine-v2"
    scan_metadata: dict = Field(default_factory=dict)
    disclaimer: str = "This is a preliminary security review and does not replace a full manual audit. Review all findings before production use."






# Monitoring Lite + Threat Intelligence Feed
class MonitoringConfigCreate(BaseModel):
    project_name: str = Field(min_length=2, max_length=160)
    contract_address: str = Field(min_length=42, max_length=42)
    chain: str = Field(default="ethereum", max_length=80)
    watch_types: list[Literal["owner_changed", "role_granted", "pause", "unpause", "upgrade", "large_mint", "treasury_movement", "custom"]] = ["owner_changed", "role_granted", "pause", "unpause", "upgrade", "large_mint"]
    alert_channels: list[Literal["dashboard", "email", "telegram", "discord", "manual"]] = ["dashboard"]
    notification_target: str | None = Field(default=None, max_length=300)
    ownership_verified: bool = False
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True
    notes: str | None = Field(default=None, max_length=4000)


class MonitoringAlertIngest(BaseModel):
    config_id: str = Field(min_length=4, max_length=120)
    event_type: Literal["owner_changed", "role_granted", "pause", "unpause", "upgrade", "large_mint", "treasury_movement", "custom"] = "custom"
    severity: Severity = "medium"
    description: str = Field(min_length=4, max_length=1200)
    tx_hash: str | None = Field(default=None, max_length=120)
    source: Literal["manual_admin", "webhook", "rpc_check"] = "manual_admin"
    evidence: dict = Field(default_factory=dict)
    real_only_acknowledged: bool = True


class MonitoringCheckRequest(BaseModel):
    config_id: str = Field(min_length=4, max_length=120)
    from_block: str | None = Field(default=None, max_length=80)
    to_block: str | None = Field(default=None, max_length=80)
    real_only_acknowledged: bool = True


class ThreatIntelCreate(BaseModel):
    title: str = Field(min_length=4, max_length=220)
    protocol_name: str | None = Field(default=None, max_length=160)
    chain: str | None = Field(default=None, max_length=80)
    category: Literal["reentrancy", "access_control", "oracle", "bridge", "wallet_drainer", "phishing", "governance", "frontend", "api", "admin_opsec", "other"] = "other"
    severity: Severity = "medium"
    summary: str = Field(min_length=10, max_length=2500)
    technical_notes: str | None = Field(default=None, max_length=4000)
    affected_project_types: list[str] = []
    relevance_tags: list[str] = []
    source_url: str | None = Field(default=None, max_length=2048)
    source_label: str | None = Field(default=None, max_length=180)
    amount_lost_usd: int | None = Field(default=None, ge=0)
    incident_date: str | None = Field(default=None, max_length=40)
    curated_by: str | None = Field(default=None, max_length=120)
    real_only_acknowledged: bool = True


class ThreatIntelQuery(BaseModel):
    project_type: str | None = Field(default=None, max_length=80)
    chain: str | None = Field(default=None, max_length=80)
    tags: list[str] = []
    limit: int = Field(default=20, ge=1, le=100)

class UnifiedUrlScanRequest(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    website_url: str = Field(min_length=8, max_length=2048)
    project_name: str | None = Field(default=None, max_length=160)
    project_type: str | None = Field(default=None, max_length=80)
    chain: str | None = Field(default=None, max_length=80)
    contract_address: str | None = Field(default=None, max_length=120)
    api_base_url: str | None = Field(default=None, max_length=2048)
    github_repo_url: str | None = Field(default=None, max_length=2048)
    solidity_code: str | None = Field(default=None, max_length=120000)
    slither_json: str | None = Field(default=None, max_length=1000000)
    semgrep_json: str | None = Field(default=None, max_length=1000000)
    aderyn_json: str | None = Field(default=None, max_length=1000000)
    openapi_json: str | None = Field(default=None, max_length=600000)
    api_observations_json: str | None = Field(default=None, max_length=600000)
    wallet_evidence_json: str | None = Field(default=None, max_length=600000)
    signature_samples_json: str | None = Field(default=None, max_length=600000)
    transaction_samples_json: str | None = Field(default=None, max_length=600000)
    business_context_json: str | None = Field(default=None, max_length=600000)
    defi_simulation_json: str | None = Field(default=None, max_length=600000)
    protocol_context_json: str | None = Field(default=None, max_length=600000)
    review_context_json: str | None = Field(default=None, max_length=600000)
    har_json: str | None = Field(default=None, max_length=1000000)
    crawler_artifact_json: str | None = Field(default=None, max_length=1000000)
    auth_test_context_json: str | None = Field(default=None, max_length=800000)
    security_tool_artifacts_json: str | None = Field(default=None, max_length=1200000)
    foundry_test_output: str | None = Field(default=None, max_length=800000)
    echidna_output_json: str | None = Field(default=None, max_length=1000000)
    invariant_artifact_json: str | None = Field(default=None, max_length=1000000)
    accuracy_feedback_json: str | None = Field(default=None, max_length=800000)
    scan_mode: str | None = Field(default="quick", max_length=32)
    deep_scan_requested: bool = False
    expert_evidence_requested: bool = False
    authorization_confirmed: bool
    real_only_acknowledged: bool = True


class GitHubRepoScanRequest(BaseModel):
    repo_url: str = Field(min_length=12, max_length=2048)
    project_name: str | None = Field(default=None, max_length=160)
    branch: str | None = Field(default=None, max_length=160)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True












# advanced website, API deep readiness, wallet risk API integration
class AdvancedWebsiteScanRequest(BaseModel):
    website_url: str = Field(min_length=8, max_length=2048)
    project_name: str | None = Field(default=None, max_length=160)
    ownership_verified: bool = False
    max_internal_pages: int = Field(default=4, ge=1, le=10)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class ApiDeepReadinessRequest(BaseModel):
    api_base_url: str | None = Field(default=None, max_length=2048)
    project_name: str | None = Field(default=None, max_length=160)
    openapi_json: str | None = Field(default=None, max_length=260000)
    api_code: str | None = Field(default=None, max_length=220000)
    notes: str | None = Field(default=None, max_length=60000)
    ownership_verified: bool = False
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class WalletRiskApiRequest(BaseModel):
    chain: str = Field(default="ethereum", max_length=80)
    token_address: str | None = Field(default=None, max_length=120)
    spender_address: str | None = Field(default=None, max_length=120)
    wallet_address: str | None = Field(default=None, max_length=120)
    approval_contract_address: str | None = Field(default=None, max_length=120)
    project_name: str | None = Field(default=None, max_length=160)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


# launch transparency, contract diff, upgrade safety
class LaunchTransparencyRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    project_type: str | None = Field(default=None, max_length=80)
    solidity_code: str | None = Field(default=None, max_length=220000)
    website_text: str | None = Field(default=None, max_length=60000)
    tokenomics_notes: str | None = Field(default=None, max_length=60000)
    liquidity_lock_evidence: str | None = Field(default=None, max_length=30000)
    metadata_freeze_evidence: str | None = Field(default=None, max_length=30000)
    owner_power_notes: str | None = Field(default=None, max_length=60000)
    multisig_enabled: bool | None = None
    timelock_enabled: bool | None = None
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class ContractDiffRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    old_code: str = Field(min_length=20, max_length=220000)
    new_code: str = Field(min_length=20, max_length=220000)
    contract_type: str | None = Field(default=None, max_length=80)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class UpgradeSafetyRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    current_code: str = Field(min_length=20, max_length=260000)
    previous_code: str | None = Field(default=None, max_length=220000)
    proxy_admin_notes: str | None = Field(default=None, max_length=30000)
    ownership_verified: bool = False
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


# Web3Guard — Contract Permission Map + Centralization Risk Report
class PermissionMapRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    solidity_code: str | None = Field(default=None, max_length=220000)
    abi_json: str | None = Field(default=None, max_length=220000)
    contract_address: str | None = Field(default=None, max_length=120)
    chain: str | None = Field(default=None, max_length=80)
    owner_address: str | None = Field(default=None, max_length=120)
    treasury_address: str | None = Field(default=None, max_length=120)
    multisig_enabled: bool | None = None
    timelock_enabled: bool | None = None
    governance_notes: str | None = Field(default=None, max_length=30000)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class DeepAnalysisRequest(BaseModel):
    solidity_code: str = Field(min_length=20, max_length=220000)
    project_name: str | None = Field(default=None, max_length=160)
    file_name: str = Field(default="Contract.sol", max_length=160)
    tools: list[Literal["mythril", "manticore", "echidna"]] = ["mythril", "manticore", "echidna"]
    scan_depth: Literal["quick", "standard", "deep"] = "quick"
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True
    ownership_verified: bool = False


class StaticAnalysisRequest(BaseModel):
    solidity_code: str = Field(min_length=20, max_length=180000)
    project_name: str | None = Field(default=None, max_length=160)
    file_name: str = Field(default="Contract.sol", max_length=160)
    tools: list[Literal["slither", "aderyn", "semgrep"]] = ["slither", "aderyn", "semgrep"]
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True

class ContractAddressScanRequest(BaseModel):
    address: str = Field(min_length=42, max_length=42)
    chain: str = Field(default="ethereum", max_length=80)
    project_name: str | None = Field(default=None, max_length=160)
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True

class ContractScanRequest(BaseModel):
    solidity_code: str = Field(min_length=20, max_length=120000)
    project_name: str | None = None
    contract_type: str | None = None
    authorization_confirmed: bool = True


class WebsiteScanRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
    project_name: str | None = None
    authorization_confirmed: bool


class ChecklistItem(BaseModel):
    key: str
    label: str
    answer: Literal["yes", "no", "unknown"] = "unknown"


class ChecklistScanRequest(BaseModel):
    project_name: str | None = None
    checklist: list[ChecklistItem] = []
    notes: str | None = Field(default=None, max_length=20000)
    authorization_confirmed: bool = True
    frontend_code: str | None = Field(default=None, max_length=120000)
    package_json: str | None = Field(default=None, max_length=60000)
    api_base_url: str | None = Field(default=None, max_length=2048)
    api_code: str | None = Field(default=None, max_length=120000)


class CombinedReportRequest(BaseModel):
    project_name: str
    reports: list[ScanResponse] = []
    preferred_language: Literal["English", "Hindi", "Hinglish"] = "English"
    include_ai: bool = True
    report_mode: Literal["founder", "developer", "investor", "pre_audit"] = "pre_audit"


class ExplanationRequest(BaseModel):
    finding: Finding
    mode: ExplanationMode = "founder"
    include_code: bool = False
    preferred_language: Literal["English", "Hindi", "Hinglish"] = "English"


class ReportExplanationRequest(BaseModel):
    report: dict
    preferred_language: Literal["English", "Hindi", "Hinglish"] = "English"
    mode: Literal["founder", "developer", "investor", "pre_audit"] = "pre_audit"


class AIExplanation(BaseModel):
    status: AIProviderStatus
    provider: str
    mode: ExplanationMode | str
    language: str = "English"
    summary: str
    business_impact: str
    developer_guidance: str
    safe_fix_direction: str
    manual_review_note: str
    confidence_note: str
    safety_note: str = "AI output is guidance only. Review before production use. This does not replace a manual audit."


# Web3Guard — Real AI Fix Assistant
class AIFixAssistantRequest(BaseModel):
    finding: Finding
    code_context: str | None = Field(default=None, max_length=220000)
    mode: Literal["safe_patch", "tests_only", "explain_only"] = "safe_patch"
    preferred_language: Literal["English", "Hindi", "Hinglish"] = "English"
    include_code: bool = False
    privacy_acknowledged: bool = False
    real_only_acknowledged: bool = True


class AIFixSuggestion(BaseModel):
    status: str
    provider: str
    model: str
    generated_at: datetime
    language: str
    finding_id: str
    finding_title: str
    finding_severity: Severity
    summary: str
    root_cause: str
    safe_patch_strategy: str
    suggested_patch_unified_diff: str = ""
    fixed_code_snippet: str = ""
    test_suggestions: list[str] = []
    validation_steps: list[str] = []
    risk_notes: list[str] = []
    manual_review_note: str
    confidence_note: str
    auto_apply_allowed: bool = False
    code_was_sent_to_provider: bool = False
    redaction_applied: bool = False
    safety_flags: list[str] = []
    safety_note: str = "AI fix suggestions are guidance only. Web3Guard AI never auto-applies production code changes and does not replace manual review."


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    contact: str = Field(min_length=5, max_length=120)
    project_name: str = Field(min_length=2, max_length=160)
    website_url: str | None = None
    contract_type: str | None = None
    selected_package: str
    package_id: str | None = None
    package_amount_inr: int | None = None
    billing_cycle: BillingCycle = "one_time"
    budget: str | None = None
    message: str | None = None
    payment_reference: str | None = None
    authorization_confirmed: bool
    consent_confirmed: bool
    preferred_language: str = "English"
    urgency: str = "Normal"


class Lead(LeadCreate):
    id: str
    created_at: datetime
    status: LeadStatus = "New"
    payment_status: PaymentStatus = "created"
    payment_intent_id: str | None = None
    payment_amount_inr: int | None = None
    payment_upi_id: str | None = None
    internal_notes: list[str] = []
    assigned_reviewer: str | None = None
    last_updated_at: datetime | None = None


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class LeadAssignUpdate(BaseModel):
    assigned_reviewer: str | None = Field(default=None, max_length=120)


class LeadPaymentUpdate(BaseModel):
    payment_status: PaymentStatus
    payment_reference: str | None = Field(default=None, max_length=160)
    payment_intent_id: str | None = Field(default=None, max_length=80)



class LeadNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=1000)
    reviewer: str | None = None


class PackagePlan(BaseModel):
    id: str
    name: str
    price_inr: int
    description: str
    deliverables: list[str]
    turnaround_time: str
    cta: str


class PaymentIntentCreate(BaseModel):
    package_id: str
    customer_name: str | None = Field(default=None, max_length=120)
    customer_email: EmailStr | None = None
    project_name: str | None = Field(default=None, max_length=160)
    billing_cycle: BillingCycle = "one_time"
    provider_preference: PaymentProviderPreference = "auto"
    user_id: str | None = Field(default=None, max_length=120)
    organization_id: str | None = Field(default=None, max_length=120)


class PaymentIntent(BaseModel):
    id: str
    created_at: datetime
    package_id: str
    package_name: str
    amount_inr: int
    amount_paise: int = 0
    currency: str = "INR"
    billing_cycle: BillingCycle
    customer_name: str | None = None
    customer_email: str | None = None
    project_name: str | None = None
    user_id: str | None = None
    organization_id: str | None = None
    provider: PaymentProvider = "upi_manual"
    provider_preference: PaymentProviderPreference = "auto"
    upi_id: str
    upi_name: str
    upi_deep_link: str | None = None
    manual_verification_required: bool = True
    razorpay_enabled: bool = False
    razorpay_key_id: str | None = None
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_signature: str | None = None
    razorpay_receipt: str | None = None
    razorpay_order_status: str | None = None
    razorpay_checkout_options: dict = Field(default_factory=dict)
    status: PaymentStatus = "created"
    verified_at: datetime | None = None
    webhook_verified_at: datetime | None = None
    subscription_id: str | None = None
    invoice_id: str | None = None
    metadata: dict = Field(default_factory=dict)
    note: str


class RazorpayVerifyRequest(BaseModel):
    payment_intent_id: str = Field(min_length=4, max_length=120)
    razorpay_order_id: str = Field(min_length=4, max_length=120)
    razorpay_payment_id: str = Field(min_length=4, max_length=120)
    razorpay_signature: str = Field(min_length=16, max_length=512)


class AdminPaymentUpdate(BaseModel):
    status: PaymentStatus
    payment_reference: str | None = Field(default=None, max_length=160)
    note: str | None = Field(default=None, max_length=1000)


class SubscriptionRecord(BaseModel):
    id: str
    created_at: datetime
    package_id: str
    plan_name: str
    billing_cycle: BillingCycle
    amount_inr: int
    currency: str = "INR"
    status: SubscriptionStatus = "pending"
    customer_name: str | None = None
    customer_email: str | None = None
    user_id: str | None = None
    organization_id: str | None = None
    payment_intent_id: str | None = None
    provider: PaymentProvider = "upi_manual"
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    activated_at: datetime | None = None
    cancelled_at: datetime | None = None
    manual_verification_required: bool = True
    notes: list[str] = []


class SubscriptionUpdate(BaseModel):
    status: SubscriptionStatus
    note: str | None = Field(default=None, max_length=1000)


class CheckoutSummary(BaseModel):
    package_id: str
    package_name: str
    amount_inr: int
    billing_cycle: BillingCycle
    upi_deep_link: str | None = None
    manual_steps: list[str]


class ScanPolicyResponse(BaseModel):
    mode: str
    allowed_methods: list[str]
    blocked_actions: list[str]
    ownership_required_for: list[str]
    consent_text: str
    private_network_blocking: bool = True
    deep_scan_available: bool = False
    note: str


class OwnershipChallengeCreate(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    website_url: str = Field(min_length=8, max_length=2048)
    method: OwnershipVerificationMethod = "well_known"
    contact_email: EmailStr | None = None


class OwnershipChallenge(BaseModel):
    id: str
    created_at: datetime
    expires_at: datetime
    project_name: str | None = None
    website_url: str
    normalized_host: str
    method: OwnershipVerificationMethod
    token: str
    status: VerificationStatus = "pending"
    dns_txt_name: str | None = None
    dns_txt_value: str | None = None
    well_known_url: str | None = None
    well_known_path: str = "/.well-known/web3guard-verify.txt"
    instructions: list[str]
    safety_note: str = "Ownership verification is for unlocking future deeper scans only. It does not mean Web3Guard AI has certified or audited the project."
    last_checked_at: datetime | None = None
    evidence: dict = Field(default_factory=dict)


class OwnershipVerifyRequest(BaseModel):
    challenge_id: str = Field(min_length=8, max_length=80)
    website_url: str = Field(min_length=8, max_length=2048)
    method: OwnershipVerificationMethod
    token: str = Field(min_length=16, max_length=160)


class OwnershipVerifyResponse(BaseModel):
    challenge_id: str
    status: VerificationStatus
    verified: bool
    checked_at: datetime
    evidence: dict = Field(default_factory=dict)
    next_steps: list[str] = []
    note: str = "Owner verification unlocks owner-approved deeper review workflows in future phases. MVP scanners remain passive/checklist/code-submitted only."


# Web3Guard — Auth + database + dashboard foundation
class UserProfile(BaseModel):
    id: str
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=160)
    company_name: str | None = Field(default=None, max_length=160)
    preferred_language: str = "English"
    plan: str = "free"
    role: str = "user"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserProfileUpsert(BaseModel):
    id: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=160)
    company_name: str | None = Field(default=None, max_length=160)
    preferred_language: str = "English"
    plan: str = "free"


class ProjectCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    name: str = Field(min_length=2, max_length=160)
    website_url: str | None = Field(default=None, max_length=2048)
    chain: str | None = Field(default=None, max_length=80)
    contract_address: str | None = Field(default=None, max_length=120)
    github_repo_url: str | None = Field(default=None, max_length=2048)
    project_type: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    owner_contact: str | None = Field(default=None, max_length=160)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    website_url: str | None = Field(default=None, max_length=2048)
    chain: str | None = Field(default=None, max_length=80)
    contract_address: str | None = Field(default=None, max_length=120)
    github_repo_url: str | None = Field(default=None, max_length=2048)
    project_type: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    owner_contact: str | None = Field(default=None, max_length=160)


class Project(ProjectCreate):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime | None = None


class ScanHistoryCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    project_id: str | None = Field(default=None, max_length=120)
    module: str = Field(min_length=2, max_length=40)
    project_name: str | None = Field(default=None, max_length=160)
    score: int | None = None
    risk_label: str | None = Field(default=None, max_length=120)
    report_id: str | None = Field(default=None, max_length=120)
    input_hash: str | None = Field(default=None, max_length=160)
    findings_count: int = 0
    critical_high_count: int = 0
    status: str = Field(default="saved", max_length=80)
    notes: str | None = Field(default=None, max_length=2000)
    payload: dict = Field(default_factory=dict)


class ScanHistoryUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)


class ScanHistoryItem(ScanHistoryCreate):
    id: str
    user_id: str
    created_at: datetime


class SavedReportCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    project_id: str | None = Field(default=None, max_length=120)
    scan_id: str | None = Field(default=None, max_length=120)
    report_id: str = Field(min_length=2, max_length=160)
    title: str = Field(min_length=2, max_length=220)
    report_hash: str | None = Field(default=None, max_length=160)
    overall_score: int | None = None
    available_score: int | None = None
    risk_label: str | None = Field(default=None, max_length=160)
    visibility: str = Field(default="private", max_length=40)
    status: str = Field(default="saved", max_length=80)
    payload: dict = Field(default_factory=dict)


class SavedReportUpdate(BaseModel):
    visibility: str | None = Field(default=None, max_length=40)
    status: str | None = Field(default=None, max_length=80)


class SavedReport(SavedReportCreate):
    id: str
    user_id: str
    created_at: datetime


class DashboardActivityItem(BaseModel):
    id: str
    type: Literal["project", "scan", "report"]
    title: str
    subtitle: str | None = None
    created_at: datetime
    project_id: str | None = None
    href: str | None = None


class ProjectDetail(BaseModel):
    project: Project
    scans: list[ScanHistoryItem] = []
    reports: list[SavedReport] = []
    activity: list[DashboardActivityItem] = []
    totals: dict = Field(default_factory=dict)


class DashboardOverview(BaseModel):
    user_id: str
    storage_mode: str
    auth_mode: str
    profile: UserProfile | None = None
    totals: dict
    projects: list[Project] = []
    recent_scans: list[ScanHistoryItem] = []
    recent_reports: list[SavedReport] = []
    activity: list[DashboardActivityItem] = []
    real_only_note: str = "Dashboard only shows records that are actually saved. No fake scan history, fake subscription, or fake audit status is generated."


# Web3Guard — Organization + Team Workspace foundation
WorkspaceRole = Literal["owner", "admin", "reviewer", "member", "viewer"]
MemberStatus = Literal["active", "invited", "removed"]
FindingTaskStatus = Literal["open", "in_progress", "fixed", "false_positive", "accepted_risk", "needs_manual_review"]
WorkspaceActivityType = Literal["organization", "member", "project", "scan", "report", "task", "comment"]


class OrganizationCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    name: str = Field(min_length=2, max_length=160)
    website_url: str | None = Field(default=None, max_length=2048)
    billing_email: EmailStr | None = None
    gst_number: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    website_url: str | None = Field(default=None, max_length=2048)
    billing_email: EmailStr | None = None
    gst_number: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)


class Organization(BaseModel):
    id: str
    owner_user_id: str
    name: str
    website_url: str | None = None
    billing_email: EmailStr | None = None
    gst_number: str | None = None
    notes: str | None = None
    plan: str = "free"
    created_at: datetime
    updated_at: datetime | None = None


class OrganizationMemberInvite(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=160)
    role: WorkspaceRole = "viewer"
    status: MemberStatus = "invited"
    note: str | None = Field(default=None, max_length=1000)


class OrganizationMemberUpdate(BaseModel):
    role: WorkspaceRole | None = None
    status: MemberStatus | None = None
    full_name: str | None = Field(default=None, max_length=160)
    note: str | None = Field(default=None, max_length=1000)


class OrganizationMember(BaseModel):
    id: str
    organization_id: str
    user_id: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    role: WorkspaceRole
    status: MemberStatus = "invited"
    invited_by_user_id: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    note: str | None = None


class FindingTaskCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    organization_id: str = Field(min_length=2, max_length=120)
    project_id: str | None = Field(default=None, max_length=120)
    scan_id: str | None = Field(default=None, max_length=120)
    report_id: str | None = Field(default=None, max_length=160)
    finding_id: str | None = Field(default=None, max_length=160)
    title: str = Field(min_length=2, max_length=220)
    module: str = Field(default="general", max_length=60)
    severity: Severity = "medium"
    status: FindingTaskStatus = "open"
    assigned_to_member_id: str | None = Field(default=None, max_length=120)
    assigned_to_user_id: str | None = Field(default=None, max_length=120)
    due_date: str | None = Field(default=None, max_length=40)
    recommendation: str | None = Field(default=None, max_length=4000)
    evidence: dict = Field(default_factory=dict)


class FindingTaskUpdate(BaseModel):
    status: FindingTaskStatus | None = None
    assigned_to_member_id: str | None = Field(default=None, max_length=120)
    assigned_to_user_id: str | None = Field(default=None, max_length=120)
    due_date: str | None = Field(default=None, max_length=40)
    recommendation: str | None = Field(default=None, max_length=4000)


class FindingTask(BaseModel):
    id: str
    organization_id: str
    project_id: str | None = None
    scan_id: str | None = None
    report_id: str | None = None
    finding_id: str | None = None
    title: str
    module: str = "general"
    severity: Severity = "medium"
    status: FindingTaskStatus = "open"
    assigned_to_member_id: str | None = None
    assigned_to_user_id: str | None = None
    due_date: str | None = None
    recommendation: str | None = None
    evidence: dict = Field(default_factory=dict)
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime | None = None


class WorkspaceCommentCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    organization_id: str = Field(min_length=2, max_length=120)
    project_id: str | None = Field(default=None, max_length=120)
    scan_id: str | None = Field(default=None, max_length=120)
    report_id: str | None = Field(default=None, max_length=160)
    finding_task_id: str | None = Field(default=None, max_length=120)
    body: str = Field(min_length=1, max_length=3000)


class WorkspaceComment(BaseModel):
    id: str
    organization_id: str
    project_id: str | None = None
    scan_id: str | None = None
    report_id: str | None = None
    finding_task_id: str | None = None
    body: str
    created_by_user_id: str
    created_at: datetime


class WorkspaceActivityItem(BaseModel):
    id: str
    organization_id: str
    type: WorkspaceActivityType
    title: str
    subtitle: str | None = None
    created_by_user_id: str | None = None
    created_at: datetime
    target_id: str | None = None


class WorkspaceOverview(BaseModel):
    organization: Organization
    current_user_role: WorkspaceRole | None = None
    members: list[OrganizationMember] = []
    projects: list[Project] = []
    scans: list[ScanHistoryItem] = []
    reports: list[SavedReport] = []
    finding_tasks: list[FindingTask] = []
    comments: list[WorkspaceComment] = []
    activity: list[WorkspaceActivityItem] = []
    totals: dict = Field(default_factory=dict)
    real_only_note: str = "Workspace data is created only from real user actions. Invites are stored as manual invite records; no fake email invite is sent."


# Bug Bounty Readiness, Public Registry/Trust Badge, Developer API/API Keys
BountyStatus = Literal["draft", "published", "paused", "closed"]
BountySubmissionStatus = Literal["submitted", "triage", "needs_more_info", "accepted", "rejected", "duplicate", "paid_manually"]
ReportRegistryStatus = Literal["active", "expired", "revoked", "superseded", "private"]
ApiKeyStatus = Literal["active", "disabled", "revoked"]


class BugBountyProgramCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    organization_id: str | None = Field(default=None, max_length=120)
    project_id: str | None = Field(default=None, max_length=120)
    project_name: str = Field(min_length=2, max_length=180)
    website_url: str | None = Field(default=None, max_length=2048)
    scope_summary: str = Field(min_length=10, max_length=5000)
    in_scope_assets: list[str] = []
    out_of_scope_assets: list[str] = []
    reward_low_inr: int | None = Field(default=None, ge=0)
    reward_medium_inr: int | None = Field(default=None, ge=0)
    reward_high_inr: int | None = Field(default=None, ge=0)
    reward_critical_inr: int | None = Field(default=None, ge=0)
    safe_harbor_text: str | None = Field(default=None, max_length=8000)
    contact_email: EmailStr | None = None
    contact_handle: str | None = Field(default=None, max_length=160)
    status: BountyStatus = "draft"
    escrow_enabled: bool = False
    authorization_confirmed: bool = True
    real_only_acknowledged: bool = True


class BugBountyProgramUpdate(BaseModel):
    status: BountyStatus | None = None
    scope_summary: str | None = Field(default=None, max_length=5000)
    safe_harbor_text: str | None = Field(default=None, max_length=8000)
    contact_email: EmailStr | None = None
    contact_handle: str | None = Field(default=None, max_length=160)


class BugBountySubmissionCreate(BaseModel):
    program_id: str = Field(min_length=4, max_length=120)
    researcher_name: str | None = Field(default=None, max_length=160)
    researcher_contact: str | None = Field(default=None, max_length=240)
    title: str = Field(min_length=4, max_length=220)
    severity_claimed: Severity = "medium"
    affected_asset: str | None = Field(default=None, max_length=600)
    description: str = Field(min_length=20, max_length=12000)
    reproduction_steps: str | None = Field(default=None, max_length=12000)
    impact: str | None = Field(default=None, max_length=8000)
    recommendation: str | None = Field(default=None, max_length=8000)
    proof_links: list[str] = []
    authorization_confirmed: bool = True
    safe_testing_acknowledged: bool = True
    real_only_acknowledged: bool = True


class BugBountySubmissionUpdate(BaseModel):
    status: BountySubmissionStatus | None = None
    triage_notes: str | None = Field(default=None, max_length=8000)
    final_severity: Severity | None = None
    reward_amount_inr: int | None = Field(default=None, ge=0)


class RegistryPublicationCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    report_id: str = Field(min_length=2, max_length=160)
    project_name: str = Field(min_length=2, max_length=180)
    report_hash: str = Field(min_length=16, max_length=160)
    score: int | None = Field(default=None, ge=0, le=100)
    risk_label: str | None = Field(default=None, max_length=160)
    summary: str | None = Field(default=None, max_length=3000)
    status: ReportRegistryStatus = "active"
    expires_at: str | None = Field(default=None, max_length=60)
    public_notes: str | None = Field(default=None, max_length=4000)
    real_only_acknowledged: bool = True


class RegistryStatusUpdate(BaseModel):
    status: ReportRegistryStatus
    reason: str | None = Field(default=None, max_length=2000)


class ApiKeyCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    organization_id: str | None = Field(default=None, max_length=120)
    name: str = Field(min_length=2, max_length=160)
    permissions: list[Literal["audit:start", "audit:read", "report:read", "registry:verify", "threat:read"]] = ["audit:read", "report:read", "registry:verify"]
    rate_limit_per_hour: int = Field(default=60, ge=1, le=5000)
    expires_at: str | None = Field(default=None, max_length=60)
    real_only_acknowledged: bool = True


class ApiKeyUpdate(BaseModel):
    status: ApiKeyStatus | None = None
    permissions: list[str] | None = None
    rate_limit_per_hour: int | None = Field(default=None, ge=1, le=5000)


class DeveloperAuditRequest(BaseModel):
    project_name: str | None = Field(default=None, max_length=160)
    solidity_code: str | None = Field(default=None, max_length=120000)
    website_url: str | None = Field(default=None, max_length=2048)
    real_only_acknowledged: bool = True

# CI/CD, Learning Center, Admin Super Panel v2
LearningProgressStatus = Literal["started", "completed", "bookmarked"]


class CiTemplateRequest(BaseModel):
    api_base_url: str | None = Field(default=None, max_length=2048)
    fail_on: Literal["critical", "high", "medium"] = "critical"
    real_only_acknowledged: bool = True


class CiConfigValidateRequest(BaseModel):
    config_text: str = Field(min_length=1, max_length=120000)
    real_only_acknowledged: bool = True


class LearningProgressCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    lesson_id: str = Field(min_length=2, max_length=120)
    status: LearningProgressStatus = "completed"
    notes: str | None = Field(default=None, max_length=2000)
    real_only_acknowledged: bool = True


class AdminFeatureFlagUpdate(BaseModel):
    enabled: bool
    note: str | None = Field(default=None, max_length=2000)
    actor: str | None = Field(default=None, max_length=160)
    real_only_acknowledged: bool = True


# Notifications, Compliance Scanner, Cross-chain Support
NotificationChannel = Literal["email", "telegram", "discord", "whatsapp", "manual"]
NotificationEventType = Literal["scan_completed", "critical_finding", "payment_received", "report_ready", "monitoring_alert", "manual_note"]
ComplianceJurisdiction = Literal["india_vda", "mica_eu", "gdpr", "fatf_aml", "general_web3"]
CrossChainFamily = Literal["evm", "solana_anchor", "move_sui_aptos"]


class NotificationPreferenceCreate(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    organization_id: str | None = Field(default=None, max_length=120)
    channels: list[NotificationChannel] = ["email"]
    event_types: list[NotificationEventType] = ["critical_finding", "report_ready", "monitoring_alert"]
    email: EmailStr | None = None
    telegram_chat_id: str | None = Field(default=None, max_length=160)
    discord_webhook_url: str | None = Field(default=None, max_length=2048)
    whatsapp_number: str | None = Field(default=None, max_length=80)
    enabled: bool = True
    real_only_acknowledged: bool = True


class NotificationSendRequest(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    event_type: NotificationEventType = "manual_note"
    channels: list[NotificationChannel] = ["manual"]
    title: str = Field(min_length=2, max_length=220)
    message: str = Field(min_length=2, max_length=5000)
    severity: Severity = "info"
    recipient_email: EmailStr | None = None
    telegram_chat_id: str | None = Field(default=None, max_length=160)
    discord_webhook_url: str | None = Field(default=None, max_length=2048)
    whatsapp_number: str | None = Field(default=None, max_length=80)
    dry_run: bool = True
    real_only_acknowledged: bool = True


class ComplianceScanRequest(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    project_name: str = Field(min_length=2, max_length=180)
    project_type: str = Field(default="web3_launch", max_length=120)
    jurisdictions: list[ComplianceJurisdiction] = ["general_web3", "india_vda"]
    has_terms: bool = False
    has_privacy_policy: bool = False
    has_refund_policy: bool = False
    collects_personal_data: bool = False
    has_data_deletion_flow: bool = False
    handles_payments_in_inr: bool = False
    has_gst_invoice_flow: bool = False
    has_kyc_flow: bool = False
    has_aml_policy: bool = False
    has_risk_disclosure: bool = False
    has_cookie_banner: bool = False
    has_incident_response: bool = False
    has_bug_bounty_safe_harbor: bool = False
    notes: str | None = Field(default=None, max_length=12000)
    real_only_acknowledged: bool = True


class CrossChainScanRequest(BaseModel):
    user_id: str | None = Field(default=None, max_length=120)
    project_name: str | None = Field(default=None, max_length=180)
    chain_family: CrossChainFamily = "evm"
    chains: list[str] = ["ethereum"]
    contract_address: str | None = Field(default=None, max_length=120)
    source_code: str | None = Field(default=None, max_length=180000)
    abi_json: str | None = Field(default=None, max_length=220000)
    notes: str | None = Field(default=None, max_length=12000)
    project_type: str = Field(default="general", max_length=120)
    real_only_acknowledged: bool = True
