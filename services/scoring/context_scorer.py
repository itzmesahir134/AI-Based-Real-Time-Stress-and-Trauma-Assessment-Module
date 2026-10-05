"""M17: Context Risk Scorer.

Computes a deterministic context risk score (0-100) based on intake factors,
active threats, prior incidents, and vulnerabilities (Spec §17).
"""

from typing import List, Union
from packages.schemas.scoring import ContextData, ContextRiskResult


def score_context(
    context: Union[ContextData, dict],
) -> ContextRiskResult:
    """Spec M17: Score situational risk from intake context.

    Formula:
        base = 20.0 (baseline for any caller seeking support)
        ongoing_threat: +30.0
        prior_case: +15.0
        vulnerabilities (minor, elderly, isolated, etc.): +10.0 per factor
        immediate_support_requested: +15.0
        score clamped to [0.0, 100.0]

    Args:
        context: ContextData object or raw dictionary.

    Returns:
        ContextRiskResult with score, completeness, and contributing risk factors.
    """
    if isinstance(context, dict):
        from .context_parser import parse_context
        ctx = parse_context(context)
    else:
        ctx = context

    base = 20.0
    active_factors: List[str] = ["baseline_support_intake"]

    if ctx.ongoing_threat:
        base += 30.0
        active_factors.append("active_ongoing_threat")

    if ctx.prior_case:
        base += 15.0
        active_factors.append("prior_incident_history")

    vuln_count = len(ctx.vulnerability_factors)
    if vuln_count > 0:
        base += vuln_count * 10.0
        for vf in ctx.vulnerability_factors:
            active_factors.append(f"vulnerability_{vf}")

    if ctx.immediate_support_requested:
        base += 15.0
        active_factors.append("immediate_escalation_requested")

    score = round(float(min(100.0, max(0.0, base))), 1)

    return ContextRiskResult(
        score=score,
        completeness=1.0,
        risk_factors=active_factors,
    )
