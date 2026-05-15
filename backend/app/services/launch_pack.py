from __future__ import annotations

from typing import Any
from app.core.config import settings

PHASE = "Phase 6.2 - UI/UX Pro Polish + Deploy Launch Pack"

REAL_ONLY_STATUS = [
    {"area": "Unified URL Scanner", "status": "live", "proof": "POST /scan/unified-url uses real website passive scan and marks missing modules Not assessed."},
    {"area": "Smart Contract Rule Engine", "status": "live", "proof": "POST /scan/contract scans pasted Solidity with local deterministic rules."},
    {"area": "Website Passive Scanner", "status": "live", "proof": "POST /scan/website performs safe HTTPS/header/robots/sitemap/script checks with SSRF guard."},
    {"area": "dApp/API/Wallet/Admin scanners", "status": "live-limited", "proof": "Checklist + pasted-code/static hints only; no exploit automation or package execution."},
    {"area": "UPI Payment", "status": "manual", "proof": "Payment intent creates UPI deep link; admin must verify settlement manually."},
    {"area": "Razorpay Auto Verification", "status": "not-enabled", "proof": "Not shown as live. Planned for next payment phase."},
    {"area": "AI", "status": "needs-api-key", "proof": "AI is disabled by default; fallback explanations are labeled as local/fallback."},
    {"area": "Certified Audit", "status": "not-offered", "proof": "All public wording says preliminary pre-audit review only."},
    {"area": "GitHub/Explorer/Slither", "status": "not-enabled", "proof": "Inputs may be recorded, but no fake scan score is generated."},
]

DEPLOY_STEPS = {
    "backend_render": [
        "Create a Render Web Service from the backend folder or use render.yaml.",
        "Set runtime to Python 3.12.8.",
        "Build command: python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt",
        "Start command: uvicorn main:app --host 0.0.0.0 --port $PORT",
        "Set FRONTEND_URL to the deployed Vercel URL.",
        "Set ADMIN_TOKEN to a long secret value.",
        "Set RAADHANEX_UPI_ID and RAADHANEX_UPI_NAME before real payment testing.",
    ],
    "frontend_vercel": [
        "Import the frontend folder in Vercel.",
        "Set NEXT_PUBLIC_API_BASE_URL to the deployed backend URL.",
        "Set NEXT_PUBLIC_UPI_ID and NEXT_PUBLIC_UPI_NAME to match backend values.",
        "Use npm install and npm run build.",
        "After deploy, open /local-qa and verify backend connectivity.",
    ],
    "production_checks": [
        "Open /health and /health/readiness on backend.",
        "Open /local-qa on frontend.",
        "Run one unified URL scan for an authorized site.",
        "Create one UPI payment intent but do not show auto-success.",
        "Submit one lead and verify it in /admin/leads.",
        "Export CSV.",
        "Generate a browser print/save-as-PDF report.",
    ],
}

LAUNCH_ROUTES = [
    {"route": "/", "purpose": "Polished trust-first landing page"},
    {"route": "/scanner/unified-url", "purpose": "Real-only URL launch surface scanner"},
    {"route": "/feature-status", "purpose": "Live/manual/not-enabled matrix"},
    {"route": "/local-qa", "purpose": "Local QA console"},
    {"route": "/launch-pack", "purpose": "Deployment, QA, and sales launch pack"},
    {"route": "/pricing", "purpose": "UPI manual payment + package funnel"},
    {"route": "/contact", "purpose": "Lead capture / manual review request"},
    {"route": "/admin/leads", "purpose": "Token-protected admin CRM"},
]

SALES_PLAYBOOK = [
    {
        "day_range": "Days 1-3",
        "goal": "Manual outreach setup",
        "actions": [
            "Create RAADHANEX/Web3Guard landing link.",
            "Prepare 3 sample reports: ERC20, NFT mint, staking.",
            "List 50 target early-stage projects from hackathons, Twitter/X, Discord, Telegram, GitHub.",
            "Send honest pitch: preliminary launch readiness, not certified audit.",
        ],
    },
    {
        "day_range": "Days 4-10",
        "goal": "First paid reports",
        "actions": [
            "Offer free URL + contract scan preview.",
            "Recommend ₹999 or ₹2,999 package only after showing real findings.",
            "Collect UPI reference and verify manually.",
            "Deliver browser-PDF/Markdown report with limitations clearly stated.",
        ],
    },
    {
        "day_range": "Days 11-30",
        "goal": "Repeatable service funnel",
        "actions": [
            "Convert repeated clients to Builder monthly subscription.",
            "Create public educational posts in Hinglish about wallet approvals, multisig, launch checklist.",
            "Ask satisfied clients for real testimonials only after delivery.",
            "Track conversion: free scan -> lead -> paid -> delivered -> follow-up scan.",
        ],
    },
]


def launch_pack() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": PHASE,
        "service": settings.app_name,
        "company": "RAADHANEX",
        "backend_url": settings.backend_url,
        "frontend_origin": settings.frontend_origin,
        "real_only_status": REAL_ONLY_STATUS,
        "deploy_steps": DEPLOY_STEPS,
        "launch_routes": LAUNCH_ROUTES,
        "sales_playbook": SALES_PLAYBOOK,
        "safe_public_wording": [
            "AI-assisted preliminary Web3 launch security review.",
            "Pre-audit readiness report, not a certified audit.",
            "Passive website checks only unless ownership is verified.",
            "UPI payments require manual verification before delivery.",
        ],
        "forbidden_public_wording": [
            "100% secure",
            "Certified audit",
            "Guaranteed exploit-free",
            "Payment successful without verification",
            "AI audited this project when AI is disabled",
        ],
    }
