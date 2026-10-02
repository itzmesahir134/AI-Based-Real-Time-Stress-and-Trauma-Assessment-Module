from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import Field
from .common import AssessmentStatus, BaseSchema, RiskBand


class ModalityScores(BaseSchema):
    """Raw 0-100 scores calculated per individual input modality."""
    voice: Optional[float] = Field(None, ge=0.0, le=100.0, description="Acoustic distress score")
    text: Optional[float] = Field(None, ge=0.0, le=100.0, description="NLP/ASR text distress score")
    self_report: Optional[float] = Field(None, ge=0.0, le=100.0, description="Questionnaire score")
    context: Optional[float] = Field(None, ge=0.0, le=100.0, description="Case history/intake context score")
    interaction: Optional[float] = Field(None, ge=0.0, le=100.0, description="Behavioral/interactional score")


class QualityFactors(BaseSchema):
    """Reliability weight multiplier (0.0 to 1.0) per modality."""
    voice: Optional[float] = Field(None, ge=0.0, le=1.0)
    text: Optional[float] = Field(None, ge=0.0, le=1.0)
    self_report: Optional[float] = Field(None, ge=0.0, le=1.0)
    context: Optional[float] = Field(None, ge=0.0, le=1.0)
    interaction: Optional[float] = Field(None, ge=0.0, le=1.0)


class ModalityContributions(BaseSchema):
    """Absolute mathematical contribution of each modality to the final SVI (sums to SVI)."""
    voice: Optional[float] = Field(None, ge=0.0)
    text: Optional[float] = Field(None, ge=0.0)
    self_report: Optional[float] = Field(None, ge=0.0)
    context: Optional[float] = Field(None, ge=0.0)
    interaction: Optional[float] = Field(None, ge=0.0)


class SVIResult(BaseSchema):
    """Persisted SVI score representation per Spec §23."""
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    svi: float = Field(..., ge=0.0, le=100.0, description="Support Vulnerability Index (0-100)")
    risk_band: RiskBand
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence")
    evidence_coverage: float = Field(..., ge=0.0, le=1.0, description="Proportion of modalities available")
    assessment_status: AssessmentStatus = AssessmentStatus.COMPLETE
    safety_override: bool = False
    model_config_version: str = Field(default="v1.0.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MasterAssessmentObject(BaseSchema):
    """Canonical assessment payload per Spec §21."""
    session_id: UUID
    assessment_status: AssessmentStatus
    svi: float = Field(..., ge=0.0, le=100.0)
    risk_band: RiskBand
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_coverage: float = Field(..., ge=0.0, le=1.0)
    safety_override: bool = False
    modality_scores: ModalityScores = Field(default_factory=ModalityScores)
    quality: QualityFactors = Field(default_factory=QualityFactors)
    contributions: ModalityContributions = Field(default_factory=ModalityContributions)
    contributors: List[str] = Field(default_factory=list, description="Top factor descriptors for human explanation")
    missing_evidence: List[str] = Field(default_factory=list, description="Uncollected or abstained modalities")
    support_recommendations: List[str] = Field(default_factory=list, description="Recommended triage paths")
