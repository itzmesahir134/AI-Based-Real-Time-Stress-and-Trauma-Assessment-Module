import pytest
from packages.schemas.assessment import RiskBand
from packages.schemas.audio import AudioQualityResult
from packages.schemas.recommendations import AssessmentExplanation, RecommendationResult
from services.recommendations.explanation_generator import generate_explanation
from services.recommendations.recommendation_engine import generate_recommendations


@pytest.mark.unit
def test_generate_explanation_standard():
    exp = generate_explanation(
        svi=68.5,
        risk_band=RiskBand.HIGH,
        confidence=0.88,
        contributors=["High self-report score (80.0)", "Elevated voice pitch variability (65.0)"],
        missing_evidence=["uncollected_interaction"],
    )

    assert isinstance(exp, AssessmentExplanation)
    assert "HIGH" in exp.summary
    assert "68.5" in exp.summary
    assert len(exp.contributors) == 2
    assert exp.confidence == 0.88


@pytest.mark.unit
def test_generate_explanation_safety_override():
    exp = generate_explanation(
        svi=42.0,  # Moderate numerical score
        risk_band=RiskBand.CRITICAL,
        confidence=0.95,
        contributors=["Moderate self-report (40.0)"],
        missing_evidence=[],
        safety_override=True,
        crisis_type="suicidal_ideation",
    )

    assert "CRITICAL" in exp.summary
    assert "Safety Override" in exp.summary
    assert "suicidal ideation" in exp.summary


@pytest.mark.unit
def test_generate_explanation_with_poor_audio():
    poor_q = AudioQualityResult(quality_score=0.25, distortion_flags=["CLIPPING_DETECTED"], clipping_ratio=0.10)
    exp = generate_explanation(
        svi=55.0,
        risk_band=RiskBand.HIGH,
        confidence=0.52,
        contributors=[],
        missing_evidence=["low_quality_voice"],
        audio_quality=poor_q,
    )

    assert len(exp.limitations) >= 2
    assert any("clipping" in lim.lower() for lim in exp.limitations)
    assert any("degraded" in lim.lower() for lim in exp.limitations)


@pytest.mark.unit
def test_generate_recommendations_critical():
    res = generate_recommendations(
        priority=RiskBand.CRITICAL,
        support_needs=["medical", "police"],
    )

    assert isinstance(res, RecommendationResult)
    assert res.priority == RiskBand.CRITICAL
    assert any("IMMEDIATE_ESCALATION" in r for r in res.recommendations)
    assert any("MEDICAL_URGENT" in r for r in res.recommendations)
    assert any("POLICE_LIAISON" in r for r in res.recommendations)


@pytest.mark.unit
def test_generate_recommendations_high():
    res = generate_recommendations(
        priority=RiskBand.HIGH,
        support_needs=["counselling", "legal"],
    )

    assert res.priority == RiskBand.HIGH
    assert any("PRIORITY_TRIAGE" in r for r in res.recommendations)
    assert any("COUNSELLING_REFERRAL" in r for r in res.recommendations)
    assert any("LEGAL_AID" in r for r in res.recommendations)


@pytest.mark.unit
def test_generate_recommendations_moderate_and_low():
    res_mod = generate_recommendations(priority=RiskBand.MODERATE)
    assert res_mod.priority == RiskBand.MODERATE
    assert any("SCHEDULED_FOLLOW_UP" in r for r in res_mod.recommendations)

    res_low = generate_recommendations(priority=RiskBand.LOW)
    assert res_low.priority == RiskBand.LOW
    assert any("INFORMATIONAL_SUPPORT" in r for r in res_low.recommendations)
