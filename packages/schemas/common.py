from enum import Enum
from pydantic import BaseModel, ConfigDict


class RiskBand(str, Enum):
    """SVI Risk Categorization per Spec §1.1 & §36."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AssessmentStatus(str, Enum):
    """Status of SVI assessment processing."""
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class BaseSchema(BaseModel):
    """Base Pydantic model with strict validation and standard configurations."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        protected_namespaces=(),
    )
