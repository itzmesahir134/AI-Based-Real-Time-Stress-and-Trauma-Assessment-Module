import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from packages.schemas import CaseCreate, CaseResponse, CaseStatus, RiskBand
from services.api.db import CaseModel, SessionModel, get_db

from services.api.security import require_role

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["Cases"],
    dependencies=[Depends(require_role("RESPONDER", "SUPERVISOR", "ADMIN"))]
)


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Spec §1.1: Opens a case for human responder triage."""
    session_result = await db.execute(select(SessionModel).where(SessionModel.id == payload.session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {payload.session_id} does not exist",
        )

    case = CaseModel(
        id=uuid.uuid4(),
        session_id=payload.session_id,
        status=CaseStatus.OPEN.value,
        priority=payload.priority.value if hasattr(payload.priority, "value") else str(payload.priority),
        assigned_to=payload.assigned_to,
        initial_notes=payload.initial_notes,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(case)
    await db.flush()
    return CaseResponse.model_validate(case)


@router.get("", response_model=List[CaseResponse])
async def list_cases(
    status_filter: Optional[CaseStatus] = Query(None, alias="status"),
    priority_filter: Optional[RiskBand] = Query(None, alias="priority"),
    db: AsyncSession = Depends(get_db),
):
    """Spec §10 & §22: Retrieves cases for the triage queue."""
    query = select(CaseModel)
    if status_filter:
        query = query.where(CaseModel.status == status_filter.value)
    if priority_filter:
        query = query.where(CaseModel.priority == priority_filter.value)

    query = query.order_by(CaseModel.created_at.desc())
    result = await db.execute(query)
    cases = result.scalars().all()
    return [CaseResponse.model_validate(c) for c in cases]


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve single case details by ID."""
    result = await db.execute(select(CaseModel).where(CaseModel.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return CaseResponse.model_validate(case)


@router.patch("/{case_id}/status", response_model=CaseResponse)
async def update_case_status(
    case_id: uuid.UUID,
    new_status: CaseStatus,
    assigned_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Update case triage status or reassign to another responder."""
    result = await db.execute(select(CaseModel).where(CaseModel.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    case.status = new_status.value
    if assigned_to:
        case.assigned_to = assigned_to
    case.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return CaseResponse.model_validate(case)
