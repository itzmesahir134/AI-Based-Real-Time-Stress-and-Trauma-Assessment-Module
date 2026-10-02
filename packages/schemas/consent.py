from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import Field
from .common import BaseSchema


class ConsentType(str, Enum):
    """Types of consent required per Spec §1.1 & §38."""
    AUDIO_RECORDING = "AUDIO_RECORDING"
    AI_ASSESSMENT = "AI_ASSESSMENT"
    DATA_RETENTION = "DATA_RETENTION"


class ConsentStatus(str, Enum):
    """Caller's consent decision."""
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    REVOKED = "REVOKED"


class ConsentCreate(BaseSchema):
    """Payload to record consent decision."""
    session_id: UUID = Field(..., description="ID of the active session")
    consent_type: ConsentType = Field(..., description="Scope of consent")
    status: ConsentStatus = Field(..., description="Granted, denied, or revoked")
    notes: Optional[str] = Field(None, description="Optional caller or responder notes")


class ConsentResponse(BaseSchema):
    """Public representation of recorded consent."""
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    consent_type: ConsentType
    status: ConsentStatus
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None
