"""Unit tests for database models, relationships, and JSON type serialization."""
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.db.models import (
    AudioAssetModel,
    AuditLogModel,
    CaseModel,
    ConsentModel,
    ContextResultModel,
    CrisisResultModel,
    HumanReviewModel,
    QualityResultModel,
    RecommendationModel,
    SelfReportModel,
    SessionModel,
    SVIResultModel,
    TextInferenceModel,
    TranscriptModel,
    TranscriptSegmentModel,
    VoiceFeatureModel,
    VoiceInferenceModel,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_all_models_instantiation_and_persistence(db_session: AsyncSession):
    """Verify that all 17 models can be created, persisted, and queried."""
    # 1. Session
    session = SessionModel(
        id=uuid.uuid4(),
        channel="webrtc",
        status="ACTIVE",
        language="hi",
    )
    db_session.add(session)
    await db_session.flush()

    # 2. Consent
    consent = ConsentModel(
        session_id=session.id,
        consent_type="biometric_audio",
        status="GRANTED",
        notes="Explicit verbal consent recorded",
    )
    db_session.add(consent)

    # 3. Case
    case = CaseModel(
        session_id=session.id,
        status="OPEN",
        priority="HIGH",
        assigned_to="agent_01",
        initial_notes="Caller reported immediate distress",
    )
    db_session.add(case)
    await db_session.flush()

    # 4. SVI Result
    svi_res = SVIResultModel(
        session_id=session.id,
        svi=78.50,
        risk_band="CRITICAL",
        confidence=0.920,
        evidence_coverage=0.850,
        assessment_status="COMPLETE",
        safety_override=False,
    )
    db_session.add(svi_res)
    await db_session.flush()

    # 5. Audit Log
    audit = AuditLogModel(
        user_id="responder_42",
        action="CASE_OPENED",
        resource_type="case",
        resource_id=str(case.id),
        details="Triage initiated",
    )
    db_session.add(audit)

    # 6. Audio Asset
    audio = AudioAssetModel(
        session_id=session.id,
        case_id=case.id,
        s3_key="audio/session_123.wav",
        duration_seconds=45.2,
        format="wav",
        sample_rate=16000,
        channels=1,
    )
    db_session.add(audio)

    # 7. Quality Result
    quality = QualityResultModel(
        session_id=session.id,
        quality_score=0.880,
        snr_estimate=24.50,
        clipping_ratio=0.010,
        speech_ratio=0.920,
        packet_loss=0.000,
        distortion_flags=["minor_background_noise"],
    )
    db_session.add(quality)
    await db_session.flush()

    # 8. Transcript
    transcript = TranscriptModel(
        session_id=session.id,
        quality_id=quality.id,
        language="hi",
        full_text="मुझे बहुत घबराहट हो रही है कृपया मदद करें",
        duration_seconds=12.40,
    )
    db_session.add(transcript)
    await db_session.flush()

    # 9. Transcript Segment
    segment = TranscriptSegmentModel(
        transcript_id=transcript.id,
        segment_order=0,
        text="मुझे बहुत घबराहट हो रही है",
        start_time=0.00,
        end_time=5.20,
        confidence=0.950,
        language="hi",
    )
    db_session.add(segment)

    # 10. Voice Feature
    voice_feat = VoiceFeatureModel(
        session_id=session.id,
        features={"pitch_mean": 210.4, "jitter": 0.018, "energy_mean": 0.045},
        schema_version="v1.0.0",
    )
    db_session.add(voice_feat)

    # 11. Voice Inference
    voice_inf = VoiceInferenceModel(
        session_id=session.id,
        score=72.00,
        confidence=0.850,
        evidence_features=["elevated_f0", "rapid_pitch_shifts"],
        model_version="v1.0.0-heuristic",
        abstained=False,
    )
    db_session.add(voice_inf)

    # 12. Text Inference
    text_inf = TextInferenceModel(
        session_id=session.id,
        score=80.00,
        confidence=0.900,
        indicators=["panic_terms", "help_plea"],
        model_version="v1.0.0-lexicon-heuristic",
        language="hi",
        abstained=False,
    )
    db_session.add(text_inf)

    # 13. Self Report
    self_rep = SelfReportModel(
        session_id=session.id,
        q1_distress=4,
        q2_safety=3,
        q3_urgency=4,
        q4_can_continue=3,
        support_needs=["counselling", "medical"],
        score=85.00,
        safety_flag=True,
        completeness=1.000,
    )
    db_session.add(self_rep)

    # 14. Context Result
    ctx_res = ContextResultModel(
        session_id=session.id,
        incident_type="domestic_distress",
        ongoing_threat=True,
        prior_case=False,
        vulnerability_factors=["isolated"],
        immediate_support_requested=True,
        score=75.00,
        completeness=1.000,
    )
    db_session.add(ctx_res)

    # 15. Crisis Result
    crisis_res = CrisisResultModel(
        session_id=session.id,
        safety_flag=True,
        crisis_type="acute_violence",
        confidence=0.880,
        evidence=["screaming", "threat_keywords"],
        rule_triggered=True,
        model_triggered=False,
    )
    db_session.add(crisis_res)

    # 16. Recommendation
    rec = RecommendationModel(
        session_id=session.id,
        svi_result_id=svi_res.id,
        priority="CRITICAL",
        recommendations=["dispatch_emergency_support", "warm_transfer_crisis_counselor"],
        explanation={"summary": "Acute crisis detected with high acoustic and linguistic distress"},
    )
    db_session.add(rec)

    # 17. Human Review
    review = HumanReviewModel(
        case_id=case.id,
        reviewer_id="supervisor_07",
        final_action="ESCALATED",
        modified_priority="CRITICAL",
        reason="Supervisor verified acute danger",
    )
    db_session.add(review)

    await db_session.commit()

    # Query back and verify persistence & JSON structures
    q_session = (await db_session.execute(select(SessionModel).where(SessionModel.id == session.id))).scalar_one()
    assert q_session.channel == "webrtc"
    assert q_session.status == "ACTIVE"

    q_quality = (await db_session.execute(select(QualityResultModel).where(QualityResultModel.session_id == session.id))).scalar_one()
    assert q_quality.distortion_flags == ["minor_background_noise"]

    q_voice_inf = (await db_session.execute(select(VoiceInferenceModel).where(VoiceInferenceModel.session_id == session.id))).scalar_one()
    assert "elevated_f0" in q_voice_inf.evidence_features

    q_rec = (await db_session.execute(select(RecommendationModel).where(RecommendationModel.session_id == session.id))).scalar_one()
    assert q_rec.priority == "CRITICAL"
    assert "dispatch_emergency_support" in q_rec.recommendations
    assert "summary" in q_rec.explanation

    q_review = (await db_session.execute(select(HumanReviewModel).where(HumanReviewModel.case_id == case.id))).scalar_one()
    assert q_review.final_action == "ESCALATED"
    assert q_review.modified_priority == "CRITICAL"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_session_cascade_deletion(db_session: AsyncSession):
    """Verify that deleting a session cascades and cleans up related child records."""
    session = SessionModel(id=uuid.uuid4(), channel="pstn", status="CLOSED")
    db_session.add(session)
    await db_session.flush()

    consent = ConsentModel(session_id=session.id, consent_type="call_recording", status="GRANTED")
    self_rep = SelfReportModel(session_id=session.id, q1_distress=2, score=50.0)
    db_session.add_all([consent, self_rep])
    await db_session.commit()

    # Verify rows exist
    q_consent = (await db_session.execute(select(ConsentModel).where(ConsentModel.session_id == session.id))).scalar_one_or_none()
    assert q_consent is not None

    # Delete session
    await db_session.delete(session)
    await db_session.commit()

    # Verify child records were cascade-deleted
    q_consent_after = (await db_session.execute(select(ConsentModel).where(ConsentModel.session_id == session.id))).scalar_one_or_none()
    assert q_consent_after is None
