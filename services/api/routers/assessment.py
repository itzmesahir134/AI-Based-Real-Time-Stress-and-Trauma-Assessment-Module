from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.schemas import (
    AssessmentRunRequest,
    MasterAssessmentObject,
    ModalityScores,
    QualityFactors,
    RiskBand,
    AssessmentStatus,
)
from services.api.db import (
    get_db,
    SessionModel,
    QualityResultModel,
    VoiceInferenceModel,
    TextInferenceModel,
    SelfReportModel,
    ContextResultModel,
    CrisisResultModel,
    SVIResultModel,
    RecommendationModel,
    CaseModel,
)
from services.api.orchestrator import run_assessment_pipeline
from services.scoring.svi_engine import calculate_svi

from services.api.security import require_role

router = APIRouter(
    prefix="/api/v1/assessment",
    tags=["Assessment Orchestrator"]
)


@router.post("/run", response_model=MasterAssessmentObject, status_code=status.HTTP_201_CREATED)
async def run_assessment(
    payload: AssessmentRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """Spec Phase 9: E2E assessment orchestrator endpoint."""
    # Validate session exists
    session_result = await db.execute(select(SessionModel).where(SessionModel.id == payload.session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {payload.session_id} does not exist",
        )
    
    try:
        return await run_assessment_pipeline(payload, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{session_id}", response_model=MasterAssessmentObject, dependencies=[Depends(require_role("RESPONDER", "SUPERVISOR", "ADMIN"))])
async def get_assessment(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Reconstructs assessment from DB for the responder UI."""
    session_result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    # Fetch all the necessary results
    svi_res = await db.execute(select(SVIResultModel).where(SVIResultModel.session_id == session_id).order_by(SVIResultModel.created_at.desc()).limit(1))
    svi_row = svi_res.scalar_one_or_none()
    if not svi_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No SVI result found for this session")

    # Modalities and Quality
    quality_res = await db.execute(select(QualityResultModel).where(QualityResultModel.session_id == session_id).order_by(QualityResultModel.created_at.desc()).limit(1))
    quality_row = quality_res.scalar_one_or_none()
    
    voice_res = await db.execute(select(VoiceInferenceModel).where(VoiceInferenceModel.session_id == session_id).order_by(VoiceInferenceModel.created_at.desc()).limit(1))
    voice_row = voice_res.scalar_one_or_none()
    
    text_res = await db.execute(select(TextInferenceModel).where(TextInferenceModel.session_id == session_id).order_by(TextInferenceModel.created_at.desc()).limit(1))
    text_row = text_res.scalar_one_or_none()
    
    sr_res = await db.execute(select(SelfReportModel).where(SelfReportModel.session_id == session_id).order_by(SelfReportModel.created_at.desc()).limit(1))
    sr_row = sr_res.scalar_one_or_none()
    
    ctx_res = await db.execute(select(ContextResultModel).where(ContextResultModel.session_id == session_id).order_by(ContextResultModel.created_at.desc()).limit(1))
    ctx_row = ctx_res.scalar_one_or_none()
    
    rec_res = await db.execute(select(RecommendationModel).where(RecommendationModel.session_id == session_id).order_by(RecommendationModel.created_at.desc()).limit(1))
    rec_row = rec_res.scalar_one_or_none()
    
    case_res = await db.execute(select(CaseModel).where(CaseModel.session_id == session_id).order_by(CaseModel.created_at.desc()).limit(1))
    case_row = case_res.scalar_one_or_none()
    
    modality_scores = ModalityScores()
    quality_factors = QualityFactors()
    
    if quality_row:
        quality_factors.voice = float(quality_row.quality_score)
        quality_factors.text = float(quality_row.quality_score)
        
    if voice_row and not voice_row.abstained:
        modality_scores.voice = float(voice_row.score)
    if text_row and not text_row.abstained:
        modality_scores.text = float(text_row.score)
    if sr_row:
        modality_scores.self_report = float(sr_row.score)
        quality_factors.self_report = float(sr_row.completeness)
    if ctx_row:
        modality_scores.context = float(ctx_row.score)
        quality_factors.context = float(ctx_row.completeness)
        
    # Re-run SVI to get contributions, contributors, missing
    svi, conf, coverage, ast_status, contrib, contrib_list, missing_ev = calculate_svi(
        modality_scores=modality_scores,
        quality_factors=quality_factors,
    )
    
    return MasterAssessmentObject(
        session_id=session_id,
        assessment_status=AssessmentStatus(svi_row.assessment_status),
        svi=float(svi_row.svi),
        risk_band=RiskBand(svi_row.risk_band),
        confidence=float(svi_row.confidence),
        evidence_coverage=float(svi_row.evidence_coverage),
        safety_override=svi_row.safety_override,
        modality_scores=modality_scores,
        quality=quality_factors,
        contributions=contrib,
        contributors=contrib_list,
        missing_evidence=missing_ev,
        support_recommendations=rec_row.recommendations if rec_row else [],
        case_id=case_row.id if case_row else None,
    )
