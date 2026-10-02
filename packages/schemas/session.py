from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import Field
from .common import BaseSchema


class ChannelEnum(str, Enum):
    """Intake channel options per Spec §0 & §19."""
    VOICE_CALL = "VOICE_CALL"
    WEB_AUDIO = "WEB_AUDIO"
    CHAT_TEXT = "CHAT_TEXT"
    WHATSAPP = "WHATSAPP"
    WALK_IN = "WALK_IN"


class SessionStatusEnum(str, Enum):
    """Session lifecycle state."""
    INITIALIZED = "INITIALIZED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class SessionCreate(BaseSchema):
    """Payload to initialize an assessment session."""
    channel: ChannelEnum = Field(..., description="Communication channel used by the caller")
    language: Optional[str] = Field("hi", description="ISO language code, e.g. hi, en, ta, te")
    caller_hash: Optional[str] = Field(None, description="One-way pseudonymous identifier for repeat callers")


class SessionResponse(BaseSchema):
    """Public representation of an assessment session."""
    id: UUID = Field(default_factory=uuid4, description="Unique session identifier")
    channel: ChannelEnum
    status: SessionStatusEnum = SessionStatusEnum.INITIALIZED
    language: Optional[str] = "hi"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = None
