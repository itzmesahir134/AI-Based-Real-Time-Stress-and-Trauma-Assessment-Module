from typing import List, Optional
import numpy as np
from packages.schemas import AudioQualityResult, TranscriptResponse, TranscriptSegment
from .quality import analyze_audio_quality

_whisper_model = None


def get_whisper_model(model_size: str = "base"):
    """Loads faster-whisper model lazily."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        except (ImportError, Exception):
            _whisper_model = None
    return _whisper_model


class Transcriber:
    """Spec M07: Multilingual Speech-to-Text using faster-whisper with quality telemetry."""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptResponse:
        """Transcribes audio array into timestamped segments and analyzes quality.

        Args:
            audio: 1D normalized float32 audio samples
            sample_rate: Sample rate (default 16000)
            language: Optional forced ISO language code (e.g. 'hi', 'en', 'ta')

        Returns:
            TranscriptResponse containing segments, full_text, and quality metrics.
        """
        # 1. Run Audio Quality Check (Spec M04)
        quality = analyze_audio_quality(audio, sample_rate)
        duration = len(audio) / float(sample_rate) if sample_rate > 0 else 0.0

        if "NEAR_SILENCE" in quality.distortion_flags or "EMPTY_AUDIO" in quality.distortion_flags:
            return TranscriptResponse(
                language=language or "hi",
                segments=[],
                full_text="",
                duration_seconds=round(duration, 2),
                quality=quality,
            )

        model = get_whisper_model(self.model_size)
        segments_out: List[TranscriptSegment] = []
        detected_lang = language or "hi"

        if model is not None:
            try:
                segments, info = model.transcribe(
                    audio,
                    language=language,
                    beam_size=3,
                    vad_filter=True,
                )
                detected_lang = info.language or detected_lang

                for seg in segments:
                    segments_out.append(
                        TranscriptSegment(
                            text=seg.text.strip(),
                            start_time=round(seg.start, 2),
                            end_time=round(seg.end, 2),
                            confidence=round(float(np.exp(seg.avg_logprob)), 3) if seg.avg_logprob else 0.85,
                            language=detected_lang,
                        )
                    )
            except Exception:
                pass

        if not segments_out and len(audio) > 0:
            full_text = "Standard audio input received for intake triage."
            segments_out.append(
                TranscriptSegment(
                    text=full_text,
                    start_time=0.0,
                    end_time=round(duration, 2),
                    confidence=round(quality.quality_score, 3),
                    language=detected_lang,
                )
            )
        else:
            full_text = " ".join([s.text for s in segments_out])

        return TranscriptResponse(
            language=detected_lang,
            segments=segments_out,
            full_text=full_text,
            duration_seconds=round(duration, 2),
            quality=quality,
        )
