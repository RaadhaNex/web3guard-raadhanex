from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Web3Guard AI by RAADHANEX"
    app_env: str = "development"
    frontend_origin: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    admin_token: str = "change-this-admin-token"
    leads_file: str = "app/data/leads.jsonl"
    raadhanex_upi_id: str = "raadhanex@upi"
    raadhanex_upi_name: str = "RAADHANEX"
    payment_mode: str = "upi_manual"  # upi_manual | razorpay | razorpay_or_upi_manual
    razorpay_enabled: bool = False
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    razorpay_api_base: str = "https://api.razorpay.com/v1"
    payment_intents_file: str = "app/data/payment_intents.jsonl"
    payment_events_file: str = "app/data/payment_events.jsonl"
    subscriptions_file: str = "app/data/subscriptions.jsonl"
    ai_enabled: bool = False
    ai_provider: str = "none"
    ai_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-5-haiku-latest"
    ai_timeout_seconds: int = 20
    ai_send_code: bool = False
    ai_fix_enabled: bool = False
    ai_fix_send_code: bool = False
    ai_fix_max_code_chars: int = 12000
    max_code_chars: int = 60000
    max_url_scan_per_hour: int = 20
    website_scan_timeout_seconds: int = 8
    website_scan_max_body_bytes: int = 750000
    website_scan_external_script_warning_threshold: int = 12
    website_scanner_user_agent: str = "Web3GuardAI-RAADHANEX-PassiveScanner/2.9 (+https://web3guard.ai; passive-check-only; owner-verification-ready)"
    ownership_challenges_file: str = "app/data/ownership_challenges.jsonl"
    max_contract_scan_per_hour: int = 60
    max_checklist_scan_per_hour: int = 80
    max_permission_map_scan_per_hour: int = 40
    max_launch_transparency_scan_per_hour: int = 40
    max_contract_diff_scan_per_hour: int = 30
    max_upgrade_safety_scan_per_hour: int = 30

    # Supabase/Auth/Database foundation.
    # Default stays local-first so the app remains runnable without cloud setup.
    storage_mode: str = "local"  # local | supabase | auto
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_verify_enabled: bool = False
    supabase_auth_required: bool = False
    local_demo_user_id: str = "local-demo-user"
    db_profiles_file: str = "app/data/db/profiles.jsonl"
    db_projects_file: str = "app/data/db/projects.jsonl"
    db_scan_history_file: str = "app/data/db/scan_history.jsonl"
    db_saved_reports_file: str = "app/data/db/saved_reports.jsonl"

    # Organization/team workspace local-first storage.
    db_organizations_file: str = "app/data/db/organizations.jsonl"
    db_org_members_file: str = "app/data/db/org_members.jsonl"
    db_finding_tasks_file: str = "app/data/db/finding_tasks.jsonl"
    db_workspace_comments_file: str = "app/data/db/workspace_comments.jsonl"
    db_workspace_activity_file: str = "app/data/db/workspace_activity.jsonl"

    # Professional/public report storage.
    public_reports_file: str = "app/data/db/public_reports.jsonl"
    public_proof_reports_file: str = "app/data/db/public_proof_reports.jsonl"
    manual_review_assignments_file: str = "app/data/db/manual_review_assignments.jsonl"
    manual_review_fix_verifications_file: str = "app/data/db/manual_review_fix_verifications.jsonl"
    manual_review_approval_events_file: str = "app/data/db/manual_review_approval_events.jsonl"
    professional_accuracy_feedback_file: str = "app/data/db/professional_accuracy_feedback.jsonl"
    professional_benchmark_regression_file: str = "app/data/db/professional_benchmark_regression_cases.jsonl"
    professional_accuracy_benchmark_file: str = "app/data/db/professional_accuracy_benchmark_runs.jsonl"
    professional_monitoring_baselines_file: str = "app/data/db/professional_monitoring_baselines.jsonl"
    professional_monitoring_events_file: str = "app/data/db/professional_monitoring_events.jsonl"
    professional_monitoring_runs_file: str = "app/data/db/professional_monitoring_runs.jsonl"
    professional_direct_level_snapshots_file: str = "app/data/db/professional_direct_level_snapshots.jsonl"
    professional_webhook_events_file: str = "app/data/db/professional_webhook_events.jsonl"
    professional_direct_level_network_enabled: bool = False
    github_webhook_secret: str | None = None
    onchain_webhook_secret: str | None = None
    professional_direct_level_min_reviewers: int = 2

    # Phase N-S: operational direct-level console, reviewer onboarding, client delivery, and safe fuzz worker.
    professional_reviewer_profiles_file: str = "app/data/db/professional_reviewer_profiles.jsonl"
    professional_client_deliveries_file: str = "app/data/db/professional_client_deliveries.jsonl"
    professional_worker_runs_file: str = "app/data/db/professional_worker_runs.jsonl"
    professional_worker_runner_enabled: bool = False
    professional_worker_allow_local_execution: bool = False
    professional_worker_network_enabled: bool = False
    professional_worker_cleanup_workspace: bool = True
    professional_worker_timeout_seconds: int = 90
    professional_worker_max_output_chars: int = 18000
    professional_worker_max_code_chars: int = 180000

    # SecureScore Pro dashboard + finding workflow persistence.
    db_finding_workflow_file: str = "app/data/db/finding_workflow.jsonl"

    # Public GitHub repository scanner.
    github_api_base: str = "https://api.github.com"
    github_api_token: str | None = None
    github_scan_timeout_seconds: int = 12
    max_github_scan_per_hour: int = 20
    max_github_files: int = 1200
    max_github_file_bytes: int = 180000
    max_github_total_bytes: int = 900000
    max_github_solidity_files: int = 8
    max_github_contract_findings_per_file: int = 10
    max_github_package_files: int = 4
    max_github_api_files: int = 16
    max_github_frontend_files: int = 16

    # verified contract address scanner via Etherscan API V2-compatible explorer API.
    etherscan_api_key: str | None = None
    polygonscan_api_key: str | None = None
    bscscan_api_key: str | None = None
    arbiscan_api_key: str | None = None
    optimismscan_api_key: str | None = None
    basescan_api_key: str | None = None
    etherscan_v2_api_base: str = "https://api.etherscan.io/v2/api"
    explorer_scan_timeout_seconds: int = 15
    max_contract_address_scan_per_hour: int = 25
    max_explorer_source_chars: int = 350000


    # real static analysis tool runner. Disabled by default so no fake tool output is shown.
    static_analysis_enabled: bool = False
    slither_enabled: bool = True
    aderyn_enabled: bool = False
    semgrep_enabled: bool = True
    slither_binary: str | None = None
    aderyn_binary: str | None = None
    semgrep_binary: str | None = None
    aderyn_command_template: str = "{binary} --root {root} --output {output}"
    audit_tool_timeout_seconds: int = 45
    audit_tool_max_output_chars: int = 16000
    audit_tool_cleanup_workspace: bool = True
    max_static_analysis_code_chars: int = 180000
    max_tool_findings_per_run: int = 30
    max_total_static_findings: int = 90
    max_static_analysis_scan_per_hour: int = 12


    # Phase 27 real worker execution dashboard/probe. Disabled by default.
    worker_execution_enabled: bool = False
    foundry_enabled: bool = False
    foundry_binary: str | None = None
    worker_probe_timeout_seconds: int = 15
    worker_probe_max_output_chars: int = 6000
    worker_require_isolated_runtime: bool = True
    worker_allow_version_probe: bool = True

    # deep analysis layer / isolated audit worker architecture. Disabled by default.
    deep_analysis_enabled: bool = False
    mythril_enabled: bool = False
    manticore_enabled: bool = False
    echidna_enabled: bool = False
    mythril_binary: str | None = None
    manticore_binary: str | None = None
    echidna_binary: str | None = None
    mythril_command_template: str = "{binary} analyze {source} -o json"
    mythril_worker_required: bool = True
    mythril_allow_local_execution: bool = False
    mythril_docker_enabled: bool = False
    mythril_docker_binary: str = "docker"
    mythril_docker_image: str | None = None
    manticore_command_template: str = "{binary} {source}"
    echidna_command_template: str = "{binary} {source} --format json"
    deep_analysis_timeout_seconds: int = 120
    deep_analysis_max_output_chars: int = 22000
    deep_analysis_cleanup_workspace: bool = True
    deep_analysis_network_enabled: bool = False
    deep_analysis_allow_dependency_install: bool = False
    max_deep_analysis_code_chars: int = 220000
    max_deep_analysis_scan_per_hour: int = 6
    max_deep_tool_findings_per_run: int = 25
    max_total_deep_findings: int = 90


    # advanced website/API/wallet intelligence.
    advanced_website_external_domain_warning_threshold: int = 10
    advanced_website_inline_script_warning_threshold: int = 8
    max_advanced_website_scan_per_hour: int = 15
    api_deep_scan_timeout_seconds: int = 8
    max_api_deep_scan_per_hour: int = 20
    max_api_deep_openapi_chars: int = 220000
    goplus_enabled: bool = False
    goplus_api_base: str = "https://api.gopluslabs.io"
    goplus_access_token: str | None = None
    wallet_risk_api_timeout_seconds: int = 10
    max_wallet_risk_api_scan_per_hour: int = 25


    # Phase 28: Real provider live integration hub. Network calls are explicit and never faked.
    provider_live_enabled: bool = True
    provider_live_network_enabled: bool = True
    provider_live_timeout_seconds: int = 12
    provider_live_max_records: int = 25
    provider_live_max_query_chars: int = 220
    provider_live_advisory_sources_enabled: bool = False
    osv_api_base: str = "https://api.osv.dev"
    nvd_api_base: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    nvd_api_key: str | None = None
    github_advisory_api_base: str = "https://api.github.com"
    cisa_kev_catalog_url: str = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


    # Phase 31 — launch validation sprint: optional live OSV/CISA dependency checks.
    launch_validation_network_enabled: bool = False
    launch_validation_timeout_seconds: int = 12
    launch_validation_max_vulnerabilities_per_package: int = 8
    launch_validation_max_cisa_matches: int = 20


    # Web3Guard Sentinel: monitoring + vulnerability intelligence core.
    sentinel_enabled: bool = True
    sentinel_live_ingestion_enabled: bool = False
    sentinel_user_monitoring_enabled: bool = True
    sentinel_admin_intelligence_enabled: bool = True
    sentinel_vulnerability_index_file: str = "app/data/db/sentinel_vulnerability_index.jsonl"
    sentinel_matches_file: str = "app/data/db/sentinel_matches.jsonl"
    sentinel_alerts_file: str = "app/data/db/sentinel_alerts.jsonl"
    sentinel_disclosures_file: str = "app/data/db/sentinel_disclosures.jsonl"
    sentinel_max_ingest_records: int = 250
    sentinel_max_intel_items: int = 100
    sentinel_max_alerts: int = 100

    # Continuous Monitoring Lite: opt-in scheduled/manual recheck model.
    continuous_monitoring_enabled: bool = True
    continuous_monitoring_network_enabled: bool = False
    continuous_monitoring_github_enabled: bool = False
    continuous_monitoring_scheduler_configured: bool = False
    continuous_monitoring_configs_file: str = "app/data/db/continuous_monitoring_configs.jsonl"
    continuous_monitoring_alerts_file: str = "app/data/db/continuous_monitoring_alerts.jsonl"
    continuous_monitoring_events_file: str = "app/data/db/continuous_monitoring_events.jsonl"
    continuous_monitoring_snapshots_file: str = "app/data/db/continuous_monitoring_snapshots.jsonl"
    continuous_monitoring_stale_report_days: int = 30
    continuous_monitoring_stale_scan_days: int = 14
    continuous_monitoring_http_timeout_seconds: int = 8
    max_continuous_monitoring_config_per_hour: int = 20
    max_continuous_monitoring_recheck_per_hour: int = 20

    # Monitoring Lite + Threat Intelligence Feed.
    monitoring_enabled: bool = False
    monitoring_rpc_enabled: bool = False
    monitoring_configs_file: str = "app/data/db/monitoring_configs.jsonl"
    monitoring_alerts_file: str = "app/data/db/monitoring_alerts.jsonl"
    monitoring_events_file: str = "app/data/db/monitoring_events.jsonl"
    monitoring_max_block_window: int = 1200
    monitoring_default_block_lookback: int = 200
    monitoring_alert_severity_for_unknown: str = "info"
    max_monitoring_config_per_hour: int = 20
    max_monitoring_check_per_hour: int = 20
    ethereum_rpc_url: str | None = None
    polygon_rpc_url: str | None = None
    bsc_rpc_url: str | None = None
    arbitrum_rpc_url: str | None = None
    optimism_rpc_url: str | None = None
    base_rpc_url: str | None = None
    avalanche_rpc_url: str | None = None

    threat_intel_enabled: bool = True
    threat_intel_live_sources_enabled: bool = False
    threat_intel_file: str = "app/data/db/threat_intel.jsonl"
    max_threat_intel_admin_writes_per_hour: int = 30

    # Bug Bounty, Public Registry, Developer API/API Keys.
    bug_bounty_programs_file: str = "app/data/db/bug_bounty_programs.jsonl"
    bug_bounty_submissions_file: str = "app/data/db/bug_bounty_submissions.jsonl"
    public_registry_file: str = "app/data/db/public_registry.jsonl"
    registry_events_file: str = "app/data/db/registry_events.jsonl"
    developer_api_keys_file: str = "app/data/db/developer_api_keys.jsonl"
    developer_api_events_file: str = "app/data/db/developer_api_events.jsonl"
    max_bug_bounty_write_per_hour: int = 30
    max_registry_write_per_hour: int = 30
    max_developer_api_key_write_per_hour: int = 20
    developer_api_enabled: bool = True
    registry_badge_base_url: str = "http://localhost:3000/registry"


    # CI/CD GitHub Action, Learning Center, Admin Super Panel v2.
    learning_progress_file: str = "app/data/db/learning_progress.jsonl"
    admin_feature_flags_file: str = "app/data/db/admin_feature_flags.jsonl"
    admin_audit_log_file: str = "app/data/db/admin_audit_log.jsonl"
    admin_super_panel_enabled: bool = True
    cicd_template_enabled: bool = True
    learning_center_enabled: bool = True

    # Notifications, Compliance Scanner, Cross-chain Support.
    notifications_enabled: bool = True
    notification_preferences_file: str = "app/data/db/notification_preferences.jsonl"
    notification_events_file: str = "app/data/db/notification_events.jsonl"
    notification_logs_file: str = "app/data/db/notification_logs.jsonl"
    smtp_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    telegram_enabled: bool = False
    telegram_bot_token: str | None = None
    telegram_default_chat_id: str | None = None
    discord_enabled: bool = False
    discord_webhook_url: str | None = None
    whatsapp_enabled: bool = False
    whatsapp_provider: str = "none"  # none | twilio | meta
    whatsapp_api_token: str | None = None
    whatsapp_from_number: str | None = None
    max_notification_write_per_hour: int = 40

    compliance_scans_file: str = "app/data/db/compliance_scans.jsonl"
    max_compliance_scan_per_hour: int = 40

    cross_chain_scans_file: str = "app/data/db/cross_chain_scans.jsonl"
    cross_chain_evm_enabled: bool = True
    cross_chain_solana_checklist_enabled: bool = True
    cross_chain_move_checklist_enabled: bool = True
    max_cross_chain_scan_per_hour: int = 40

    # Platform Security Hardening + Final Production QA.
    security_headers_enabled: bool = True
    hsts_enabled: bool = False
    hsts_max_age: int = 31536000
    security_csp: str = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    max_request_body_bytes: int = 5_000_000
    rate_limit_backend: str = "memory"  # memory | redis/upstash later
    default_data_retention_days: int = 90
    production_launch_acknowledged: bool = False

    # Platform Security Hardening + Final Production Launch QA.
    production_hardening_enabled: bool = True
    security_headers_enabled: bool = True
    strict_transport_security_max_age: int = 31536000
    content_security_policy_report_only: bool = True
    production_cors_lock_required: bool = True
    data_retention_enabled: bool = True
    code_upload_retention_days: int = 7
    scan_history_retention_days: int = 180
    lead_retention_days: int = 365
    payment_record_retention_days: int = 1825
    audit_log_retention_days: int = 365
    user_data_delete_request_sla_days: int = 30
    backup_policy_enabled: bool = False
    backup_provider: str = "manual"
    sentry_enabled: bool = False
    sentry_dsn: str | None = None
    uptime_monitoring_enabled: bool = False
    production_launch_approved: bool = False
    final_qa_owner: str = "RAADHANEX admin"
    final_qa_last_run_file: str = "app/data/db/final_qa_runs.jsonl"
    security_audit_log_file: str = "app/data/db/security_audit_log.jsonl"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
