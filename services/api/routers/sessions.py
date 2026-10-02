import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from packages.schemas import SessionCreate, SessionResponse, SessionStatusEnum
from services.api.db import SessionModel, get_db

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Spec §1.1: Initializes a new assessment session."""
    session = SessionModel(
        id=uuid.uuid4(),
        channel=payload.channel.value if hasattr(payload.channel, "value") else str(payload.channel),
        status=SessionStatusEnum.INITIALIZED.value,
        language=payload.language or "hi",
        created_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()
    return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve session details by ID."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return SessionResponse.model_validate(session)


@router.patch("/{session_id}/close", response_model=SessionResponse)
async def close_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Mark session as completed."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session.status = SessionStatusEnum.COMPLETED.value
    session.closed_at = datetime.now(timezone.utc)
    await db.flush()
    return SessionResponse.model_validate(session)
