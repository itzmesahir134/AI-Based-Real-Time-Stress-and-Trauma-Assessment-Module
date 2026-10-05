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


class VoiceFeatureVector(BaseSchema):
    """Spec M08: Acoustic and prosodic feature vector extracted from speech segments."""
    pitch_mean: float = Field(0.0, description="Mean fundamental frequency (F0) in Hz")
    pitch_std: float = Field(0.0, description="Standard deviation of F0 in Hz")
    pitch_range: float = Field(0.0, description="Pitch range (max - min F0) in Hz")
    speech_rate_syl_per_sec: float = Field(0.0, description="Estimated syllables per second of active speech")
    pause_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Ratio of pause duration to total duration")
    pause_count: int = Field(0, ge=0, description="Count of silent pauses >= 200ms")
    energy_mean: float = Field(0.0, description="Mean frame RMS energy")
    energy_std: float = Field(0.0, description="Standard deviation of frame RMS energy")
    jitter: float = Field(0.0, description="Relative pitch period perturbation (jitter)")
    shimmer: float = Field(0.0, description="Relative amplitude perturbation (shimmer)")
    mfcc_mean: List[float] = Field(default_factory=list, description="Mean of 13 MFCC coefficients")
    mfcc_std: List[float] = Field(default_factory=list, description="Std dev of 13 MFCC coefficients")
    spectral_centroid_mean: float = Field(0.0, description="Mean spectral centroid in Hz")
    zcr_mean: float = Field(0.0, description="Mean zero crossing rate")
    voiced_fraction: float = Field(0.0, ge=0.0, le=1.0, description="Proportion of speech frames that are voiced")
    feature_schema_version: str = Field(default="v1.0.0", description="Feature extractor schema version")


class VoiceInferenceResult(BaseSchema):
    """Spec M09: Voice distress model inference result."""
    score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Acoustic distress score (0-100), None if abstained")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Inference confidence (0.0 to 1.0)")
    evidence_features: List[str] = Field(default_factory=list, description="Top contributory acoustic indicators")
    model_version: str = Field(default="v1.0.0-heuristic", description="Model or heuristic scoring version")
    abstained: bool = Field(False, description="True if audio quality was too low or speech insufficient to score")

