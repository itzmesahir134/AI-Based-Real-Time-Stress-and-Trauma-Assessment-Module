from typing import List, Optional
from uuid import UUID
from pydantic import Field
from .common import BaseSchema


class AudioQualityResult(BaseSchema):
    """Spec M04: Audio reliability metrics before acoustic/ASR inference."""
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall reliability score (0.0 to 1.0)")
    snr_estimate: Optional[float] = Field(None, description="Signal-to-noise ratio in decibels (dB)")
    clipping_ratio: float = Field(default=0.0, ge=0.0, le=1.0, description="Proportion of clipped samples")
    speech_ratio: float = Field(default=1.0, ge=0.0, le=1.0, description="Proportion of frames containing speech")
    packet_loss: Optional[float] = Field(None, ge=0.0, le=1.0, description="Estimated WebRTC/PSTN packet loss")
    distortion_flags: List[str] = Field(default_factory=list, description="Quality issue flags")


class SpeechSegment(BaseSchema):
    """Spec M05: Output of Voice Activity Detection (VAD)."""
    start_time: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end_time: float = Field(..., ge=0.0, description="End timestamp in seconds")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="VAD confidence score")


class TranscriptSegment(BaseSchema):
    """Spec M07: Individual timestamped utterance segment."""
    text: str = Field(..., description="Recognized speech text")
    start_time: float = Field(..., ge=0.0, description="Start offset in seconds")
    end_time: float = Field(..., ge=0.0, description="End offset in seconds")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="ASR token/segment confidence")
    language: str = Field(default="hi", description="ISO language detected or specified")


class TranscriptResponse(BaseSchema):
    """Spec M07: Complete speech transcription output with quality assessment."""
    session_id: Optional[UUID] = None
    language: str = "hi"
    segments: List[TranscriptSegment] = Field(default_factory=list)
    full_text: str = ""
    duration_seconds: float = 0.0
    quality: Optional[AudioQualityResult] = None
