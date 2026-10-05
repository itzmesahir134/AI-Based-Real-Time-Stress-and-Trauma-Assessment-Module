"""M24: Support Recommendation Engine.

Implements the deterministic triage routing matrix mapping clinical priority and
caller-reported support needs to structured recommendations (Spec §24).
"""

from typing import List, Optional
from packages.schemas.assessment import RiskBand
from packages.schemas.recommendations import AssessmentExplanation, RecommendationResult


def generate_recommendations(
    priority: RiskBand,
    support_needs: Optional[List[str]] = None,
    safety_override: bool = False,
    explanation: Optional[AssessmentExplanation] = None,
) -> RecommendationResult:
    """Spec M24: Support recommendation generator.

    Args:
        priority: Assessed triage priority band (LOW, MODERATE, HIGH, CRITICAL).
        support_needs: List of self-reported support domains requested by caller.
        safety_override: Whether priority resulted from a safety override.
        explanation: AssessmentExplanation object from M25.

    Returns:
        RecommendationResult with prioritized action list and explanation.
    """
    needs = [str(n).lower() for n in (support_needs or [])]
    recs: List[str] = []

    # 1. CRITICAL priority routing
    if priority == RiskBand.CRITICAL or safety_override:
        recs.append("IMMEDIATE_ESCALATION: Assign to senior human responder immediately.")
        recs.append("SAFETY_PROTOCOL: Keep caller on the line; initiate emergency location verification.")
        recs.append("EMERGENCY_DISPATCH: Coordinate with emergency services / 112 / women helpline dispatch.")
        if any(w in needs for w in ["medical", "hospital", "doctor"]):
            recs.append("MEDICAL_URGENT: Alert emergency medical services (EMS).")
        if any(w in needs for w in ["shelter", "stay", "home"]):
            recs.append("SHELTER_URGENT: Arrange immediate emergency crisis shelter placement.")
        if any(w in needs for w in ["legal", "police", "fir"]):
            recs.append("POLICE_LIAISON: Direct dispatch to local women protection unit.")

    # 2. HIGH priority routing
    elif priority == RiskBand.HIGH:
        recs.append("PRIORITY_TRIAGE: Human case reviewer assignment within 15 minutes.")
        if any(w in needs for w in ["counselling", "counseling", "therapy", "mental"]):
            recs.append("COUNSELLING_REFERRAL: Connect with trauma-informed psychological counsellor.")
        if any(w in needs for w in ["medical", "doctor"]):
            recs.append("MEDICAL_REFERRAL: Arrange clinic evaluation and forensic medical care.")
        if any(w in needs for w in ["legal", "court", "lawyer"]):
            recs.append("LEGAL_AID: Refer to legal support cell for protection order and rights guidance.")
        if any(w in needs for w in ["shelter", "safe_home"]):
            recs.append("SHELTER_COORDINATION: Assess safe short-term shelter options.")
        if not recs or len(recs) == 1:
            recs.append("GENERAL_HIGH_SUPPORT: Comprehensive multi-agency victim support review.")

    # 3. MODERATE priority routing
    elif priority == RiskBand.MODERATE:
        recs.append("SCHEDULED_FOLLOW_UP: Assign case officer for follow-up contact within 24 hours.")
        recs.append("COMMUNITY_SUPPORT: Provide directory of local crisis centers and helplines.")
        recs.append("SAFETY_PLANNING: Share digital safety planning guide and emergency contact protocols.")

    # 4. LOW priority routing
    else:
        recs.append("INFORMATIONAL_SUPPORT: Provide psychoeducation, rights information, and self-care resources.")
        recs.append("ROUTINE_INTAKE: Log intake case; inform caller of 24/7 hotline availability.")

    # Provide fallback explanation if not supplied
    if explanation is None:
        explanation = AssessmentExplanation(
            summary=f"Automated triage assessment: Priority {priority.value}.",
            contributors=[],
            limitations=[],
            missing_evidence=[],
            confidence=0.80,
        )

    return RecommendationResult(
        priority=priority,
        recommendations=recs,
        explanation=explanation,
    )
