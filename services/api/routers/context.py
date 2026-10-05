from fastapi import APIRouter, HTTPException, status
from packages.schemas import ContextData, ContextRiskResult
from services.scoring import score_context

router = APIRouter(prefix="/api/v1/context", tags=["Context Risk"])


@router.post("", response_model=ContextRiskResult, status_code=status.HTTP_200_OK)
async def submit_context_data(context: ContextData):
    """Spec M17: Evaluates contextual risk factors and active threats."""
    try:
        return score_context(context)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to score context data: {str(e)}",
        )
