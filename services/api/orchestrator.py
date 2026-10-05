import asyncio
import base64
import uuid
from datetime import datetime, timezone
import traceback

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from packages.schemas import (
    AssessmentRunRequest,
    MasterAssessmentObject,
    ModalityScores,
    QualityFactors,
    SelfReportQuestionnaire,
    ContextData,
    AssessmentStatus,
    CaseStatus,
)
from services.audio_worker import (
    analyze_audio_quality,
    detect_voice_activity,
    preprocess_audio,
    extract_voice_features,
    Transcriber,
)
from services.inference import (
    evaluate_voice_distress,
    normalize_transcript,
    extract_linguistic_features,
    classify_text_distress,
)
from services.scoring import (
    score_self_report,
    score_context,
    detect_crisis,
    calculate_svi,
    classify_risk_band,
    apply_safety_override,
)
from services.recommendations import (
    generate_explanation,
    generate_recommendations,
)
from services.api.db import (
    AuditLogModel,
    CaseModel,
    ContextResultModel,
    CrisisResultModel,
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
from services.audio_worker.preprocessor import bytes_to_pcm_array

transcriber = Transcriber()

async def run_assessment_pipeline(payload: AssessmentRunRequest, db: AsyncSession) -> MasterAssessmentObject:
    """End-to-End orchestrator for the assessment pipeline (Spec §21, §54)."""
    
    session_id = payload.session_id
    lang = payload.language or "hi"
    now = datetime.now(timezone.utc)

    # State objects to hold results
    voice_quality = 0.0
    voice_abstained = True
    text_abstained = True
    audio = None
    sample_rate = 16000

    db_quality = None
    db_transcript = None
    db_transcript_segments = []
    db_voice_features = None
    
    voice_inference = None
    text_inference = None
    self_report_res = None
    context_res = None
    crisis_res = None

    modality_scores = ModalityScores()
    quality_factors = QualityFactors()

    # Step 1: Decode Audio
    if payload.audio_base64:
        try:
            audio_bytes = base64.b64decode(payload.audio_base64)
            audio, sample_rate = bytes_to_pcm_array(audio_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode audio base64: {e}")

    # Steps 2-8: Audio processing
    if audio is not None and len(audio) > 0:
        # Preprocess
        cleaned_audio, sr = preprocess_audio(audio, orig_sr=sample_rate)
        
        # M04: Quality
        quality = analyze_audio_quality(cleaned_audio, sample_rate=sr)
        voice_quality = float(quality.quality_score)
        
        db_quality = QualityResultModel(
            id=uuid.uuid4(),
            session_id=session_id,
            quality_score=quality.quality_score,
            snr_estimate=quality.snr_estimate,
            clipping_ratio=quality.clipping_ratio,
            speech_ratio=quality.speech_ratio,
            packet_loss=quality.packet_loss,
            distortion_flags=quality.distortion_flags,
            created_at=now,
        )

        quality_factors.voice = voice_quality
        quality_factors.text = voice_quality # Assuming text quality correlates with audio quality from ASR
        
        if voice_quality > 0.15:
            voice_abstained = False
            text_abstained = False
            
            # M05 VAD
            segments = detect_voice_activity(cleaned_audio, sample_rate=sr)
            
            if not segments:
                voice_abstained = True
                text_abstained = True
            else:
                # M08 Features
                features = extract_voice_features(cleaned_audio, speech_segments=segments, sample_rate=sr)
                db_voice_features = VoiceFeatureModel(
                    id=uuid.uuid4(),
                    session_id=session_id,
                    features=features.model_dump(),
                    created_at=now,
                )
                
                # M07 ASR
                transcript_resp = transcriber.transcribe(cleaned_audio, sample_rate=sr, language=lang)
                db_transcript = TranscriptModel(
                    id=uuid.uuid4(),
                    session_id=session_id,
                    quality_id=db_quality.id,
                    language=lang,
                    full_text=transcript_resp.full_text,
                    duration_seconds=transcript_resp.duration_seconds,
                    created_at=now,
                )
                for i, seg in enumerate(transcript_resp.segments):
                    db_transcript_segments.append(TranscriptSegmentModel(
                        id=uuid.uuid4(),
                        transcript_id=db_transcript.id,
                        segment_order=i,
                        text=seg.text,
                        start_time=seg.start_time,
                        end_time=seg.end_time,
                        confidence=seg.confidence,
                        language=lang,
                    ))

    # Parallel inferences
    async def run_voice():
        if voice_abstained or db_voice_features is None:
            return None
        return evaluate_voice_distress(
            features=features,
            quality=quality,
            language=lang
        )

    async def run_text():
        if text_abstained or db_transcript is None or not db_transcript.full_text.strip():
            return None
        norm_trans = normalize_transcript(db_transcript.full_text, language=lang)
        ling_feat = extract_linguistic_features(norm_trans, language=lang)
        return classify_text_distress(transcript=norm_trans, features=ling_feat, language=lang)
    
    async def run_crisis():
        transcript_text = db_transcript.full_text if db_transcript else ""
        sr_obj = SelfReportQuestionnaire(**payload.self_report) if payload.self_report else None
        ctx_obj = ContextData(**payload.context) if payload.context else None
        return detect_crisis(transcript=transcript_text, self_report=sr_obj, context=ctx_obj)
        
    async def run_self_report():
        if not payload.self_report:
            return None
        sr_obj = SelfReportQuestionnaire(**payload.self_report)
        return score_self_report(sr_obj)

    async def run_context():
        if not payload.context:
            return None
        ctx_obj = ContextData(**payload.context)
        return score_context(ctx_obj)

    voice_inference, text_inference, crisis_res, self_report_res, context_res = await asyncio.gather(
        run_voice(),
        run_text(),
        run_crisis(),
        run_self_report(),
        run_context()
    )

    # Map to DB Models
    db_voice_inference = VoiceInferenceModel(
        id=uuid.uuid4(), session_id=session_id, abstained=True, created_at=now
    )
    if voice_inference:
        db_voice_inference.abstained = False
        db_voice_inference.score = voice_inference.score
        db_voice_inference.confidence = voice_inference.confidence
        db_voice_inference.evidence_features = voice_inference.evidence_features
        modality_scores.voice = voice_inference.score

    db_text_inference = TextInferenceModel(
        id=uuid.uuid4(), session_id=session_id, abstained=True, language=lang, created_at=now
    )
    if text_inference:
        db_text_inference.abstained = False
        db_text_inference.score = text_inference.score
        db_text_inference.confidence = text_inference.confidence
        db_text_inference.indicators = text_inference.indicators
        modality_scores.text = text_inference.score

    db_crisis_result = CrisisResultModel(
        id=uuid.uuid4(),
        session_id=session_id,
        safety_flag=crisis_res.safety_flag if crisis_res else False,
        crisis_type=crisis_res.crisis_type if crisis_res else None,
        confidence=crisis_res.confidence if crisis_res else 0.0,
        evidence=crisis_res.evidence if crisis_res else [],
        rule_triggered=crisis_res.rule_triggered if crisis_res else False,
        model_triggered=crisis_res.model_triggered if crisis_res else False,
        created_at=now,
    )

    db_self_report = None
    if self_report_res:
        sr_payload = payload.self_report
        db_self_report = SelfReportModel(
            id=uuid.uuid4(),
            session_id=session_id,
            q1_distress=sr_payload.get('q1_distress', 0),
            q2_safety=sr_payload.get('q2_safety', 0),
            q3_urgency=sr_payload.get('q3_urgency', 0),
            q4_can_continue=sr_payload.get('q4_can_continue', 0),
            support_needs=sr_payload.get('support_needs', []),
            score=self_report_res.score,
            safety_flag=self_report_res.safety_flag,
            completeness=self_report_res.completeness,
            created_at=now,
        )
        modality_scores.self_report = self_report_res.score
        quality_factors.self_report = self_report_res.completeness

    db_context_result = None
    if context_res:
        ctx_payload = payload.context
        db_context_result = ContextResultModel(
            id=uuid.uuid4(),
            session_id=session_id,
            incident_type=ctx_payload.get('incident_type', 'unknown'),
            ongoing_threat=ctx_payload.get('ongoing_threat', False),
            prior_case=ctx_payload.get('prior_case', False),
            vulnerability_factors=ctx_payload.get('vulnerability_factors', []),
            immediate_support_requested=ctx_payload.get('immediate_support_requested', False),
            score=context_res.score,
            completeness=context_res.completeness,
            created_at=now,
        )
        modality_scores.context = context_res.score
        quality_factors.context = context_res.completeness

    # SVI Fusion
    svi, conf, coverage, status, contrib, contrib_list, missing_ev = calculate_svi(
        modality_scores=modality_scores,
        quality_factors=quality_factors,
    )
    
    base_risk_band = classify_risk_band(svi)
    final_risk_band, safety_override = apply_safety_override(
        base_risk_band=base_risk_band, 
        crisis=crisis_res or CrisisResult()
    )
    
    db_svi_result = SVIResultModel(
        id=uuid.uuid4(),
        session_id=session_id,
        svi=svi,
        risk_band=final_risk_band.value,
        confidence=conf,
        evidence_coverage=coverage,
        assessment_status=status.value,
        safety_override=safety_override,
        created_at=now,
    )

    # Explanation & Recommendations
    explanation = generate_explanation(
        svi=svi,
        risk_band=final_risk_band,
        confidence=conf,
        contributors=contrib_list,
        missing_evidence=missing_ev,
        safety_override=safety_override,
        crisis_type=crisis_res.crisis_type if crisis_res else None,
    )
    
    support_needs = payload.self_report.get('support_needs', []) if payload.self_report else []
    
    rec_result = generate_recommendations(
        priority=final_risk_band,
        support_needs=support_needs,
        safety_override=safety_override,
        explanation=explanation,
    )

    db_recommendation = RecommendationModel(
        id=uuid.uuid4(),
        session_id=session_id,
        svi_result_id=db_svi_result.id,
        priority=final_risk_band.value,
        recommendations=rec_result.recommendations,
        explanation=explanation.model_dump(),
        created_at=now,
    )

    # Open Case
    db_case = CaseModel(
        id=uuid.uuid4(),
        session_id=session_id,
        status=CaseStatus.OPEN.value,
        priority=final_risk_band.value,
        initial_notes=f"Auto-generated case for session {session_id}",
        created_at=now,
        updated_at=now,
    )
    
    # Audit Log
    db_audit_log = AuditLogModel(
        id=uuid.uuid4(),
        action="ASSESSMENT_COMPLETED",
        resource_type="CASE",
        resource_id=str(db_case.id),
        details=f"E2E Orchestrator completed. SVI: {svi}, Risk: {final_risk_band.value}",
        timestamp=now,
    )

    # Write all to DB
    if db_quality: db.add(db_quality)
    if db_transcript: db.add(db_transcript)
    for seg in db_transcript_segments: db.add(seg)
    if db_voice_features: db.add(db_voice_features)
    
    db.add(db_voice_inference)
    db.add(db_text_inference)
    db.add(db_crisis_result)
    
    if db_self_report: db.add(db_self_report)
    if db_context_result: db.add(db_context_result)
    
    db.add(db_svi_result)
    db.add(db_recommendation)
    db.add(db_case)
    db.add(db_audit_log)
    
    await db.commit()

    return MasterAssessmentObject(
        session_id=session_id,
        assessment_status=status,
        svi=svi,
        risk_band=final_risk_band,
        confidence=conf,
        evidence_coverage=coverage,
        safety_override=safety_override,
        modality_scores=modality_scores,
        quality=quality_factors,
        contributions=contrib,
        contributors=contrib_list,
        missing_evidence=missing_ev,
        support_recommendations=rec_result.recommendations,
        case_id=db_case.id,
    )
