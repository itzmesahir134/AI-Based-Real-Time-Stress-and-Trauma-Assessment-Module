"""M25: Assessment Explanation Generator.

Constructs clinical, transparent, and structured explanations of triage decisions (Spec §25).
Explains why an SVI priority was assigned, identifies dominant contributors,
and explicitly highlights evidence limitations.
"""

from typing import List, Optional
from packages.schemas.assessment import RiskBand
from packages.schemas.audio import AudioQualityResult
from packages.schemas.recommendations import AssessmentExplanation


def generate_explanation(
    svi: float,
    risk_band: RiskBand,
    confidence: float,
    contributors: List[str],
    missing_evidence: List[str],
    safety_override: bool = False,
    crisis_type: Optional[str] = None,
    audio_quality: Optional[AudioQualityResult] = None,
) -> AssessmentExplanation:
    """Spec M25: Generate structured clinical explanation of assessment.

    Args:
        svi: Final calculated SVI score (0-100).
        risk_band: Assigned priority band.
        confidence: Calibrated confidence (0-1).
        contributors: Ranked descriptors of primary contributors.
        missing_evidence: List of uncollected or abstained modalities.
        safety_override: Whether priority was forced by safety override.
        crisis_type: Identified crisis category if safety override was triggered.
        audio_quality: Optional audio quality metrics for noting acoustic limitations.

    Returns:
        AssessmentExplanation object with summary, contributors, limitations, and confidence.
    """
    # 1. Construct clinical summary
    if safety_override:
        crisis_desc = crisis_type.replace("_", " ") if crisis_type else "acute safety threat"
        summary = (
            f"Assessment triage priority is escalated to CRITICAL via Safety Override due to detected {crisis_desc}. "
            f"Continuous SVI score is {svi:.1f} (Confidence: {confidence * 100:.0f}%)."
        )
    else:
        summary = (
            f"Assessment indicates {risk_band.value} triage urgency with an SVI score of {svi:.1f} "
            f"(Confidence: {confidence * 100:.0f}%)."
        )

    # 2. Extract limitations
    limitations: List[str] = []
    if audio_quality is not None:
        if audio_quality.quality_score < 0.40:
            limitations.append(
                f"Acoustic reliability degraded (quality={audio_quality.quality_score:.2f}, flags={audio_quality.distortion_flags})"
            )
        if audio_quality.clipping_ratio > 0.05:
            limitations.append(f"Audio exhibits clipping distortion ({audio_quality.clipping_ratio * 100:.1f}% samples)")

    if confidence < 0.60:
        limitations.append(
            f"Moderate overall confidence ({confidence * 100:.0f}%) due to partial modality coverage or noisy data."
        )

    for item in missing_evidence:
        if "low_quality" in item:
            limitations.append(f"Modality abstained due to insufficient signal: {item}")

    return AssessmentExplanation(
        summary=summary,
        contributors=contributors,
        limitations=limitations,
        missing_evidence=missing_evidence,
        confidence=confidence,
    )
