from typing import Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from packages.schemas import (
    MasterAssessmentObject,
    ModalityScores,
    QualityFactors,
    RiskBand,
)
from services.recommendations import generate_explanation, generate_recommendations
from services.scoring import apply_safety_override, calculate_svi, classify_risk_band

router = APIRouter(prefix="/api/v1/svi", tags=["SVI Scoring"])


class SVICalculateRequest(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    modality_scores: ModalityScores
    quality: Optional[QualityFactors] = None
    force_safety_flag: bool = False
    crisis_type: Optional[str] = None
    support_needs: list[str] = Field(default_factory=list)


@router.post("/calculate", response_model=MasterAssessmentObject, status_code=status.HTTP_200_OK)
async def calculate_svi_assessment(req: SVICalculateRequest):
    """Spec M21: Compute composite SVI, apply clinical safety override, and generate triage plan."""
    try:
        (
            svi,
            confidence,
            coverage,
            assessment_status,
            contributions,
            contributors,
            missing_evidence,
        ) = calculate_svi(
            modality_scores=req.modality_scores,
            quality_factors=req.quality,
        )

        base_risk_band = classify_risk_band(svi)

        # Evaluate safety override
        from packages.schemas.scoring import CrisisResult
        crisis = CrisisResult(safety_flag=req.force_safety_flag, crisis_type=req.crisis_type)
        final_risk_band, safety_override_applied = apply_safety_override(base_risk_band, crisis)

        # Generate explanation & recommendations
        explanation = generate_explanation(
            svi=svi,
            risk_band=final_risk_band,
            confidence=confidence,
            contributors=contributors,
            missing_evidence=missing_evidence,
            safety_override=safety_override_applied,
            crisis_type=req.crisis_type,
        )

        rec_result = generate_recommendations(
            priority=final_risk_band,
            support_needs=req.support_needs,
            safety_override=safety_override_applied,
            explanation=explanation,
        )

        return MasterAssessmentObject(
            session_id=req.session_id,
            assessment_status=assessment_status,
            svi=svi,
            risk_band=final_risk_band,
            confidence=confidence,
            evidence_coverage=coverage,
            safety_override=safety_override_applied,
            modality_scores=req.modality_scores,
            quality=req.quality or QualityFactors(),
            contributions=contributions,
            contributors=contributors,
            missing_evidence=missing_evidence,
            support_recommendations=rec_result.recommendations,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SVI calculation failed: {str(e)}",
        )
