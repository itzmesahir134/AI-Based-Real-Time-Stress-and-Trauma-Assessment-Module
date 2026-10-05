from fastapi import APIRouter, HTTPException, status
from packages.schemas import SelfReportQuestionnaire, SelfReportResult
from services.scoring import score_self_report

router = APIRouter(prefix="/api/v1/self-report", tags=["Self-Report"])


@router.post("", response_model=SelfReportResult, status_code=status.HTTP_200_OK)
async def submit_self_report(questionnaire: SelfReportQuestionnaire):
    """Spec M15: Score self-report questionnaire and verify safety triggers."""
    try:
        return score_self_report(questionnaire)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to score self-report questionnaire: {str(e)}",
        )
