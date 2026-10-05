from typing import List, Optional
from pydantic import Field
from .common import BaseSchema


class SelfReportQuestionnaire(BaseSchema):
    """Spec M14: 5-item self-report questionnaire responses."""
    q1_distress: int = Field(0, ge=0, le=4, description="0=calm, 4=extremely distressed")
    q2_safety: int = Field(0, ge=0, le=4, description="0=completely safe, 4=in immediate danger")
    q3_urgency: int = Field(0, ge=0, le=4, description="0=no hurry, 4=yes immediately")
    q4_can_continue: int = Field(0, ge=0, le=4, description="0=yes easily, 4=no I cannot")
    support_needs: List[str] = Field(default_factory=list, description="counselling, medical, legal, police, shelter, other")


class SelfReportResult(BaseSchema):
    """Spec M15: Evaluated self-report distress score and flags."""
    score: float = Field(..., ge=0.0, le=100.0, description="Self-report distress score (0-100)")
    completeness: float = Field(..., ge=0.0, le=1.0, description="Completeness ratio of answered questions")
    safety_flag: bool = Field(False, description="Flagged if caller indicates immediate danger or critical urgency")
    support_needs: List[str] = Field(default_factory=list, description="Requested support domains")


class ContextData(BaseSchema):
    """Spec M16: Case history and situational context intake."""
    incident_type: str = Field(default="unknown", description="Type of incident e.g. domestic_violence, harassment")
    ongoing_threat: bool = Field(False, description="Whether threat is active/ongoing")
    prior_case: bool = Field(False, description="Whether previous incidents/reports exist")
    vulnerability_factors: List[str] = Field(default_factory=list, description="e.g. minor, elderly, disability, isolated")
    immediate_support_requested: bool = Field(False, description="Caller specifically requests immediate triage")


class ContextRiskResult(BaseSchema):
    """Spec M17: Evaluated context risk score."""
    score: float = Field(..., ge=0.0, le=100.0, description="Contextual risk score (0-100)")
    completeness: float = Field(..., ge=0.0, le=1.0, description="Data availability ratio for context factors")
    risk_factors: List[str] = Field(default_factory=list, description="Active risk multiplier descriptions")


class CrisisResult(BaseSchema):
    """Spec M13: Crisis and imminent harm detection result."""
    safety_flag: bool = Field(False, description="True if any immediate safety/crisis criterion is met")
    crisis_type: Optional[str] = Field(None, description="immediate_threat, suicidal_ideation, medical_emergency, acute_violence")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in crisis detection")
    evidence: List[str] = Field(default_factory=list, description="Triggering phrases or indicators")
    rule_triggered: bool = Field(False, description="Triggered by deterministic rules")
    model_triggered: bool = Field(False, description="Triggered by ML model")
