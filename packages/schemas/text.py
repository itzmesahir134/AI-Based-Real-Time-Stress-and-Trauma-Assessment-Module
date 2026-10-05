from typing import List, Optional
from pydantic import Field
from .common import BaseSchema


class NormalizedSegment(BaseSchema):
    """Spec M10: Normalized utterance segment."""
    text: str = Field(..., description="Normalized segment text")
    start_time: float = Field(0.0, ge=0.0, description="Start offset in seconds")
    end_time: float = Field(0.0, ge=0.0, description="End offset in seconds")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="ASR segment confidence")


class NormalizedTranscript(BaseSchema):
    """Spec M10: Fully normalized transcript preserving emotional cues and hesitations."""
    text: str = Field(..., description="Cleaned, normalized full text")
    segments: List[NormalizedSegment] = Field(default_factory=list, description="Normalized segment list")
    normalization_flags: List[str] = Field(default_factory=list, description="Applied normalization flags")
    language: str = Field(default="en", description="Language code")


class LinguisticFeatures(BaseSchema):
    """Spec M11: Extracted linguistic distress indicators across psychological dimensions."""
    fear_indicators: List[str] = Field(default_factory=list, description="Detected fear and panic terms")
    threat_indicators: List[str] = Field(default_factory=list, description="Detected acute threat/violence terms")
    helplessness_indicators: List[str] = Field(default_factory=list, description="Detected helplessness/entrapment terms")
    urgency_indicators: List[str] = Field(default_factory=list, description="Detected high-urgency markers")
    negative_affect_indicators: List[str] = Field(default_factory=list, description="Detected acute negative affect terms")
    help_request_indicators: List[str] = Field(default_factory=list, description="Explicit help/rescue requests")
    self_blame_indicators: List[str] = Field(default_factory=list, description="Self-blame and worthlessness terms")
    uncertainty_indicators: List[str] = Field(default_factory=list, description="Disorientation/uncertainty terms")
    indicator_count: int = Field(0, ge=0, description="Total count of active distress indicators")


class TextInferenceResult(BaseSchema):
    """Spec M12: Text distress inference result."""
    score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Text distress score (0-100), None if abstained")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence in text distress prediction (0.0 to 1.0)")
    indicators: List[str] = Field(default_factory=list, description="Dominant linguistic indicator categories detected")
    model_version: str = Field(default="v1.0.0-lexicon-heuristic", description="Model version or classifier identifier")
    language: str = Field(default="en", description="Evaluated transcript language")
    abstained: bool = Field(False, description="True if transcript was empty or insufficient to evaluate")
