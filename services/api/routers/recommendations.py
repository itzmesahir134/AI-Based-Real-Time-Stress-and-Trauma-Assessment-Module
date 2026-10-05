from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from packages.schemas import RecommendationResult, RiskBand
from services.recommendations import generate_recommendations

router = APIRouter(prefix="/api/v1/support", tags=["Support Recommendations"])


class RecommendationRequest(BaseModel):
    priority: RiskBand
    support_needs: List[str] = Field(default_factory=list)
    safety_override: bool = False


@router.post("/recommend", response_model=RecommendationResult, status_code=status.HTTP_200_OK)
async def get_support_recommendations(req: RecommendationRequest):
    """Spec M24: Generate triage routing and referral action recommendations."""
    try:
        return generate_recommendations(
            priority=req.priority,
            support_needs=req.support_needs,
            safety_override=req.safety_override,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate recommendations: {str(e)}",
        )
