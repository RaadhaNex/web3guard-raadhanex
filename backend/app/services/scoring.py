from app.models.schemas import Finding

PENALTIES = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
    "info": 1,
}

CONFIDENCE_MULTIPLIER = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.4,
}

WEIGHTS = {
    "contract": 0.35,
    "website": 0.15,
    "dapp": 0.15,
    "api": 0.15,
    "wallet": 0.10,
    "admin_opsec": 0.10,
}

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


def risk_label(score: int) -> str:
    if score >= 90:
        return "Launch Ready with Minor Notes"
    if score >= 75:
        return "Low Risk, Fix Recommended"
    if score >= 60:
        return "Medium Risk, Fix Before Launch"
    if score >= 40:
        return "High Risk, Manual Review Recommended"
    return "Critical Launch Risk"


def severity_breakdown(findings: list[Finding]) -> dict[str, int]:
    return {severity: sum(1 for finding in findings if finding.severity == severity) for severity in SEVERITY_ORDER}


def score_findings(findings: list[Finding]) -> int:
    """Score from 100 using severity penalty, confidence multiplier, and category cap.

    Category cap prevents one repeated pattern from destroying the full score.
    This is a launch-readiness score, not an audit guarantee.
    """
    category_caps: dict[str, float] = {}
    total_penalty = 0.0
    for finding in findings:
        category = finding.category or finding.title.lower().split()[0]
        raw = PENALTIES.get(finding.severity, 1) * CONFIDENCE_MULTIPLIER.get(finding.confidence, 0.7)
        used = category_caps.get(category, 0.0)
        allowed = max(0.0, 40.0 - used)
        applied = min(raw, allowed)
        category_caps[category] = used + applied
        total_penalty += applied
    return max(0, min(100, round(100 - total_penalty)))


def priority_actions(findings: list[Finding], limit: int = 5) -> list[str]:
    ordered = sorted(
        findings,
        key=lambda f: (SEVERITY_ORDER.index(f.severity), {"high": 0, "medium": 1, "low": 2}.get(f.confidence, 3)),
    )
    actions: list[str] = []
    for finding in ordered:
        action = f"{finding.severity.upper()}: {finding.title} — {finding.recommendation}"
        if action not in actions:
            actions.append(action)
        if len(actions) >= limit:
            break
    return actions


def combine_scores(module_scores: dict[str, int]) -> dict:
    assessed = {module: score for module, score in module_scores.items() if score is not None and module in WEIGHTS}
    if not assessed:
        return {"overall_score": None, "available_score": None, "risk_label": "Not assessed"}

    weight_sum = sum(WEIGHTS[module] for module in assessed)
    weighted = sum(assessed[module] * WEIGHTS[module] for module in assessed) / weight_sum
    score = round(weighted)
    return {
        "overall_score": score if len(assessed) == len(WEIGHTS) else None,
        "available_score": score,
        "risk_label": risk_label(score),
        "assessed_modules": list(assessed.keys()),
        "missing_modules": [module for module in WEIGHTS if module not in assessed],
    }
