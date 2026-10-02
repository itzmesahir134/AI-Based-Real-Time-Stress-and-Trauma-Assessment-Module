from typing import List
import numpy as np
from packages.schemas import SpeechSegment


def detect_voice_activity(
    audio: np.ndarray,
    sample_rate: int = 16000,
    frame_duration_ms: int = 30,
    speech_threshold_ratio: float = 2.5,
    min_speech_duration_ms: int = 120,
    hangover_ms: int = 200,
) -> List[SpeechSegment]:
    """Spec M05: Voice Activity Detection (VAD) segmenter.
    Extracts speech timestamps and confidence while filtering silence.

    Args:
        audio: 1D normalized float32 array
        sample_rate: Sampling rate (Hz)
        frame_duration_ms: Frame window in milliseconds
        speech_threshold_ratio: Multiplier above background noise floor to classify as speech
        min_speech_duration_ms: Minimum duration of a valid speech burst
        hangover_ms: Duration to hold speech state across brief micro-pauses

    Returns:
        List of SpeechSegment with start_time, end_time, and confidence.
    """
    if len(audio) == 0:
        return []

    # Ensure float32 normalized
    audio = audio.astype(np.float32)

    frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
    hop_size = frame_size // 2

    if len(audio) < frame_size:
        return [SpeechSegment(start_time=0.0, end_time=round(len(audio) / sample_rate, 3), confidence=0.8)]

    # Compute short-time frame energy
    num_frames = (len(audio) - frame_size) // hop_size + 1
    energies = np.array([
        np.sum(audio[i * hop_size : i * hop_size + frame_size] ** 2)
        for i in range(num_frames)
    ])

    # Dynamic noise floor estimate (lowest 15% quantile)
    noise_floor = float(np.percentile(energies, 15))
    threshold = max(noise_floor * speech_threshold_ratio, 1e-5)

    is_speech = energies > threshold

    # Apply hangover to smooth micro-pauses
    hangover_frames = int((hangover_ms / 1000.0) / (hop_size / sample_rate))
    smoothed_speech = np.copy(is_speech)
    hold = 0
    for i in range(len(smoothed_speech)):
        if is_speech[i]:
            hold = hangover_frames
        elif hold > 0:
            smoothed_speech[i] = True
            hold -= 1

    # Extract continuous segments
    segments: List[SpeechSegment] = []
    in_speech = False
    start_frame = 0

    for i, active in enumerate(smoothed_speech):
        if active and not in_speech:
            in_speech = True
            start_frame = i
        elif not active and in_speech:
            in_speech = False
            start_time = (start_frame * hop_size) / sample_rate
            end_time = (i * hop_size + frame_size) / sample_rate
            duration_ms = (end_time - start_time) * 1000.0
            if duration_ms >= min_speech_duration_ms:
                seg_energy = np.mean(energies[start_frame : i + 1])
                conf = float(np.clip(seg_energy / (threshold * 3.0), 0.5, 0.99))
                segments.append(
                    SpeechSegment(
                        start_time=round(start_time, 3),
                        end_time=round(end_time, 3),
                        confidence=round(conf, 3),
                    )
                )

    if in_speech:
        start_time = (start_frame * hop_size) / sample_rate
        end_time = len(audio) / sample_rate
        if (end_time - start_time) * 1000.0 >= min_speech_duration_ms:
            segments.append(
                SpeechSegment(
                    start_time=round(start_time, 3),
                    end_time=round(end_time, 3),
                    confidence=0.85,
                )
            )

    return segments
