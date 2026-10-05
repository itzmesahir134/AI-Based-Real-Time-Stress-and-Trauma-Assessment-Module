import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.schemas import HumanReviewCreate, HumanReviewResponse, CaseResponse, CaseStatus
from services.api.db import CaseModel, HumanReviewModel, AuditLogModel, get_db

from services.api.security import require_role

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["Human Review (M26)"],
    dependencies=[Depends(require_role("RESPONDER", "SUPERVISOR", "ADMIN"))]
)


@router.post("/{case_id}/review", response_model=HumanReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_human_review(
    case_id: uuid.UUID,
    payload: HumanReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    """Spec M26: Human review and final triage override endpoint."""
    result = await db.execute(select(CaseModel).where(CaseModel.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    review = HumanReviewModel(
        id=uuid.uuid4(),
        case_id=case_id,
        reviewer_id=payload.reviewer_id,
        final_action=payload.final_action,
        modified_priority=payload.modified_priority.value if payload.modified_priority else None,
        reason=payload.reason,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(review)

    if payload.modified_priority:
        case.priority = payload.modified_priority.value
    
    if payload.final_action == "CLOSE":
        case.status = CaseStatus.CLOSED.value
    else:
        case.status = CaseStatus.IN_REVIEW.value
    
    case.updated_at = datetime.now(timezone.utc)

    # Add audit log
    audit_log = AuditLogModel(
        id=uuid.uuid4(),
        user_id=payload.reviewer_id,
        action=f"M26_REVIEW_{payload.final_action}",
        resource_type="CASE",
        resource_id=str(case_id),
        details=f"Priority: {payload.modified_priority}. Reason: {payload.reason}",
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(review)
    
    return HumanReviewResponse(
        id=review.id,
        case_id=review.case_id,
        reviewer_id=review.reviewer_id,
        final_action=review.final_action,
        modified_priority=payload.modified_priority,
        reason=review.reason,
        created_at=review.reviewed_at,
    )


@router.get("/{case_id}/review", response_model=List[HumanReviewResponse])
async def list_case_reviews(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all reviews for a case."""
    result = await db.execute(
        select(HumanReviewModel)
        .where(HumanReviewModel.case_id == case_id)
        .order_by(HumanReviewModel.reviewed_at.desc())
    )
    reviews = result.scalars().all()
    return [
        HumanReviewResponse(
            id=r.id,
            case_id=r.case_id,
            reviewer_id=r.reviewer_id,
            final_action=r.final_action,
            modified_priority=r.modified_priority,
            reason=r.reason,
            created_at=r.reviewed_at,
        ) for r in reviews
    ]
