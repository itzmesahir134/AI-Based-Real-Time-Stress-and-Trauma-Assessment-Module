from typing import List
from pydantic import Field
from .common import BaseSchema, RiskBand


class AssessmentExplanation(BaseSchema):
    """Spec M25: Transparent clinical explanation of SVI triage rationale."""
    summary: str = Field(..., description="High-level clinical summary of the assessment")
    contributors: List[str] = Field(default_factory=list, description="Primary modality factors driving the score")
    limitations: List[str] = Field(default_factory=list, description="Data reliability limitations or acoustic degradation")
    missing_evidence: List[str] = Field(default_factory=list, description="Modalities uncollected or abstained")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated assessment confidence")


class RecommendationResult(BaseSchema):
    """Spec M24: Triage action plan and referrals."""
    priority: RiskBand = Field(..., description="Assigned priority band after safety overrides")
    recommendations: List[str] = Field(default_factory=list, description="Ordered triage action recommendations")
    explanation: AssessmentExplanation = Field(..., description="Clinical rationale for the recommendations")
