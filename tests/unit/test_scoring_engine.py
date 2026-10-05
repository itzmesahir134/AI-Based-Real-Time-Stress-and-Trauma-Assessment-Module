import pytest
from packages.schemas.assessment import (
    AssessmentStatus,
    ModalityContributions,
    ModalityScores,
    QualityFactors,
    RiskBand,
)
from packages.schemas.audio import AudioQualityResult, VoiceInferenceResult
from packages.schemas.scoring import (
    ContextData,
    ContextRiskResult,
    CrisisResult,
    SelfReportQuestionnaire,
    SelfReportResult,
)
from packages.schemas.text import TextInferenceResult
from services.scoring.context_parser import parse_context
from services.scoring.context_scorer import score_context
from services.scoring.crisis_detector import detect_crisis
from services.scoring.evidence_quality import estimate_evidence_quality
from services.scoring.risk_classifier import classify_risk_band
from services.scoring.safety_override import apply_safety_override
from services.scoring.self_report_scorer import score_self_report
from services.scoring.svi_engine import calculate_svi


@pytest.mark.unit
def test_self_report_scoring():
    # Calm
    calm = SelfReportQuestionnaire(q1_distress=0, q2_safety=0, q3_urgency=0, q4_can_continue=0)
    res_calm = score_self_report(calm)
    assert res_calm.score == 0.0
    assert res_calm.safety_flag is False

    # Immediate danger flag
    danger = SelfReportQuestionnaire(q1_distress=4, q2_safety=4, q3_urgency=4, q4_can_continue=2)
    res_danger = score_self_report(danger)
    assert res_danger.score > 85.0
    assert res_danger.safety_flag is True

    # Weighted check: (0.3*2 + 0.35*3 + 0.25*1 + 0.1*0)/4.0 = 1.9/4.0 = 0.475 * 100 = 47.5
    mixed = SelfReportQuestionnaire(q1_distress=2, q2_safety=3, q3_urgency=1, q4_can_continue=0)
    res_mixed = score_self_report(mixed)
    assert res_mixed.score == 47.5
    assert res_mixed.safety_flag is True  # q2 >= 3 triggers safety flag


@pytest.mark.unit
def test_context_scoring():
    # Standard intake baseline
    ctx_base = ContextData()
    res_base = score_context(ctx_base)
    assert res_base.score == 20.0

    # Ongoing threat + prior case + minor + immediate support
    ctx_high = ContextData(
        ongoing_threat=True,
        prior_case=True,
        vulnerability_factors=["minor", "isolated"],
        immediate_support_requested=True,
    )
    # base 20 + ongoing 30 + prior 15 + vuln 20 + immediate 15 = 100.0
    res_high = score_context(ctx_high)
    assert res_high.score == 100.0
    assert "active_ongoing_threat" in res_high.risk_factors


@pytest.mark.unit
def test_crisis_detection_suicidal_and_threat():
    # Suicide ideation trigger
    res_suicide = detect_crisis(transcript="I don't know what to do, I want to kill myself tonight.")
    assert res_suicide.safety_flag is True
    assert res_suicide.crisis_type == "suicidal_ideation"
    assert res_suicide.rule_triggered is True

    # Lethal weapon threat
    res_threat = detect_crisis(transcript="He has a gun and he is threatening to shoot me!")
    assert res_threat.safety_flag is True
    assert res_threat.crisis_type == "immediate_threat"

    # Self-report danger trigger
    sr_danger = SelfReportQuestionnaire(q2_safety=4)
    res_sr = detect_crisis(self_report=sr_danger)
    assert res_sr.safety_flag is True

    # Neutral conversation
    res_neutral = detect_crisis(transcript="Can I schedule a consultation for Friday morning?")
    assert res_neutral.safety_flag is False


@pytest.mark.unit
def test_safety_override():
    base_band = RiskBand.LOW
    crisis_active = CrisisResult(safety_flag=True, crisis_type="immediate_threat")
    final_band, overridden = apply_safety_override(base_band, crisis_active)

    assert final_band == RiskBand.CRITICAL
    assert overridden is True

    crisis_inactive = CrisisResult(safety_flag=False)
    final_band_2, overridden_2 = apply_safety_override(RiskBand.MODERATE, crisis_inactive)
    assert final_band_2 == RiskBand.MODERATE
    assert overridden_2 is False


@pytest.mark.unit
def test_evidence_quality_estimation():
    audio_q = AudioQualityResult(quality_score=0.90)
    voice_inf = VoiceInferenceResult(score=70.0, confidence=0.80)
    text_inf = TextInferenceResult(score=65.0, confidence=0.95)
    sr_res = SelfReportResult(score=80.0, completeness=1.0)
    ctx_res = ContextRiskResult(score=60.0, completeness=1.0)

    q = estimate_evidence_quality(
        audio_quality=audio_q,
        voice_inference=voice_inf,
        text_inference=text_inf,
        self_report_result=sr_res,
        context_result=ctx_res,
    )

    assert isinstance(q, QualityFactors)
    assert q.voice == round(0.90 * 0.80, 3)  # 0.72
    assert q.text == 0.95
    assert q.self_report == 1.0
    assert q.context == 1.0


@pytest.mark.unit
def test_svi_fusion_engine_full_modalities():
    scores = ModalityScores(
        voice=70.0,
        text=60.0,
        self_report=80.0,
        context=50.0,
        interaction=40.0,
    )
    quality = QualityFactors(
        voice=0.9,
        text=0.95,
        self_report=1.0,
        context=1.0,
        interaction=0.8,
    )

    svi, conf, coverage, status, contribs, contributors, missing = calculate_svi(
        modality_scores=scores,
        quality_factors=quality,
    )

    assert 60.0 <= svi <= 75.0
    assert coverage == 1.0
    assert status == AssessmentStatus.COMPLETE
    assert conf >= 0.80
    assert isinstance(contribs, ModalityContributions)

    # Contributions must sum closely to final SVI
    contrib_sum = sum(
        val for val in [contribs.voice, contribs.text, contribs.self_report, contribs.context, contribs.interaction]
        if val is not None
    )
    assert abs(contrib_sum - svi) <= 0.2


@pytest.mark.unit
def test_svi_missing_modalities_excluded_from_denominator():
    # Only self-report and context available; voice, text, interaction missing
    scores = ModalityScores(
        self_report=80.0,
        context=60.0,
    )
    quality = QualityFactors(
        self_report=1.0,
        context=1.0,
    )

    svi, conf, coverage, status, contribs, contributors, missing = calculate_svi(
        modality_scores=scores,
        quality_factors=quality,
    )

    # SR weight=0.30, CTX weight=0.15. Weighted average = (0.3*80 + 0.15*60)/(0.3+0.15) = (24 + 9)/0.45 = 73.3
    assert 72.0 <= svi <= 74.0
    # Missing modalities must NOT pull the score down to near-zero!
    assert svi > 70.0
    assert coverage == round((0.30 + 0.15) / 1.0, 2)  # 0.45
    assert status == AssessmentStatus.PARTIAL
    assert "uncollected_voice" in missing
    assert "uncollected_text" in missing


@pytest.mark.unit
def test_risk_band_classifier():
    assert classify_risk_band(15.0) == RiskBand.LOW
    assert classify_risk_band(35.0) == RiskBand.MODERATE
    assert classify_risk_band(65.0) == RiskBand.HIGH
    assert classify_risk_band(85.0) == RiskBand.CRITICAL
