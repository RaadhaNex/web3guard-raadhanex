from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import SecurityHeadersMiddleware
from app.routers import admin, admin_super, agency_launch, ai, billing_final, bug_bounty, cicd, community_review, compliance, security_passport, continuous_monitoring, crosschain, database, developer_api, engine_depth, eon, india_launch, provider_readiness, provider_live, trust_metrics, public_trust_page, report_verification, dashboard_workflow, production_deployment_qa, final_qa, launch_final, launch_validation, scanner_results, worker_runs, payment_validation, health, leads, launch, learning, monitoring, notifications, ownership, packages, payments, public_beta, public_registry, qa, reports, scans, securescore, security_copilot, security_hardening, security_tests, sentinel, threat_intel, trust, trust_readiness, worker_execution, workspace

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="AI-assisted Web3 launch security review platform by RAADHANEX. AI-assisted preliminary Web3 launch security review.",
    docs_url=None if settings.app_env.lower() in {"production", "staging"} else "/docs",
    redoc_url=None if settings.app_env.lower() in {"production", "staging"} else "/redoc",
    openapi_url=None if settings.app_env.lower() in {"production", "staging"} else "/openapi.json",
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ai.router)
app.include_router(packages.router)
app.include_router(payments.router)
app.include_router(billing_final.router)
app.include_router(qa.router)
app.include_router(scans.router)
app.include_router(reports.router)
app.include_router(securescore.router)
app.include_router(leads.router)
app.include_router(launch.router)
app.include_router(database.router)
app.include_router(workspace.router)
app.include_router(worker_execution.router)
app.include_router(agency_launch.router)
app.include_router(admin.router)
app.include_router(trust.router)
app.include_router(trust_readiness.router)
app.include_router(ownership.router)
app.include_router(monitoring.router)
app.include_router(continuous_monitoring.router)
app.include_router(community_review.router)
app.include_router(security_passport.router)
app.include_router(threat_intel.router)
app.include_router(sentinel.router)
app.include_router(bug_bounty.router)
app.include_router(public_registry.router)
app.include_router(public_beta.router)
app.include_router(developer_api.router)
app.include_router(engine_depth.router)
app.include_router(eon.router)
app.include_router(india_launch.router)
app.include_router(provider_readiness.router)
app.include_router(provider_live.router)
app.include_router(trust_metrics.router)
app.include_router(public_trust_page.router)
app.include_router(report_verification.router)
app.include_router(dashboard_workflow.router)
app.include_router(production_deployment_qa.router)
app.include_router(cicd.router)
app.include_router(learning.router)
app.include_router(admin_super.router)
app.include_router(notifications.router)
app.include_router(compliance.router)
app.include_router(crosschain.router)
app.include_router(security_hardening.router)
app.include_router(security_tests.router)
app.include_router(security_copilot.router)
app.include_router(security_hardening.alias_router)
app.include_router(final_qa.router)
app.include_router(final_qa.alias_router)
app.include_router(launch_final.router)
app.include_router(launch_validation.router)
app.include_router(scanner_results.router)
app.include_router(worker_runs.router)
app.include_router(payment_validation.router)


@app.get("/")
def root():
    return {
        "ok": True,
        "service": settings.app_name,
        "env": settings.app_env,
        "status": "production-ready",
        "disclaimer": "Preliminary security review only. Not a certified audit.",
    }
