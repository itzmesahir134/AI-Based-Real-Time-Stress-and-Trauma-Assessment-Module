import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from packages.schemas import ConsentCreate, ConsentResponse
from services.api.db import ConsentModel, SessionModel, get_db

router = APIRouter(prefix="/api/v1/consent", tags=["Consent"])


@router.post("", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def record_consent(
    payload: ConsentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Spec §1.1 & §38: Records a caller's consent decision for a session."""
    session_result = await db.execute(select(SessionModel).where(SessionModel.id == payload.session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {payload.session_id} does not exist",
        )

    consent = ConsentModel(
        id=uuid.uuid4(),
        session_id=payload.session_id,
        consent_type=payload.consent_type.value if hasattr(payload.consent_type, "value") else str(payload.consent_type),
        status=payload.status.value if hasattr(payload.status, "value") else str(payload.status),
        notes=payload.notes,
        granted_at=datetime.now(timezone.utc),
    )
    db.add(consent)
    await db.flush()
    return ConsentResponse.model_validate(consent)


@router.get("/{session_id}", response_model=List[ConsentResponse])
async def get_session_consents(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all consent records for a given session."""
    result = await db.execute(select(ConsentModel).where(ConsentModel.session_id == session_id))
    consents = result.scalars().all()
    return [ConsentResponse.model_validate(c) for c in consents]
