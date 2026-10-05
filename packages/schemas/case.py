from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import Field
from .common import BaseSchema, RiskBand


class CaseStatus(str, Enum):
    """Lifecycle status of a triage case in the responder queue."""
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CaseCreate(BaseSchema):
    """Payload to open a new case for human triage."""
    session_id: UUID = Field(..., description="Associated assessment session ID")
    priority: RiskBand = Field(default=RiskBand.LOW, description="Initial priority level")
    initial_notes: Optional[str] = Field(None, description="Initial triage notes")
    assigned_to: Optional[str] = Field(None, description="Responder username or ID if pre-assigned")


class CaseResponse(BaseSchema):
    """Representation of a case presented in the responder dashboard."""
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    status: CaseStatus = CaseStatus.OPEN
    priority: RiskBand = RiskBand.LOW
    assigned_to: Optional[str] = None
    initial_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumanReviewCreate(BaseSchema):
    """Payload for human review M26."""
    reviewer_id: str
    final_action: str = Field(..., description="CONFIRM, ESCALATE, DOWNGRADE, CLOSE")
    modified_priority: Optional[RiskBand] = None
    reason: Optional[str] = None

class HumanReviewResponse(BaseSchema):
    id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    reviewer_id: str
    final_action: str
    modified_priority: Optional[RiskBand] = None
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
