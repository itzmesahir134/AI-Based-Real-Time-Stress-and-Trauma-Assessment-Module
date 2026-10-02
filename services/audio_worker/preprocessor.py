import io
import wave
from typing import Tuple
import numpy as np
from scipy import signal


def bytes_to_pcm_array(audio_bytes: bytes) -> Tuple[np.ndarray, int]:
    """Decodes raw audio bytes (WAV or raw 16-bit PCM) into a float32 numpy array and sample rate."""
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            num_channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

            if sample_width == 2:
                audio = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 4:
                audio = np.frombuffer(raw_data, dtype=np.int32).astype(np.float32) / 2147483648.0
            elif sample_width == 1:
                audio = (np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            else:
                audio = np.frombuffer(raw_data, dtype=np.float32)

            if num_channels > 1:
                audio = audio.reshape(-1, num_channels).mean(axis=1)

            return audio, sample_rate
    except wave.Error:
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return audio, 16000


def preprocess_audio(
    audio: np.ndarray,
    orig_sr: int,
    target_sr: int = 16000,
    target_peak: float = 0.95,
) -> Tuple[np.ndarray, int]:
    """Spec M06: Safe audio normalization and resampling without destructive artifacts.

    Args:
        audio: 1D audio sample array
        orig_sr: Source sampling rate
        target_sr: Target sampling rate (16kHz standard for ASR and VAD)
        target_peak: Safe target peak amplitude (avoids digital clipping)

    Returns:
        Tuple of (preprocessed_audio, sample_rate)
    """
    if len(audio) == 0:
        return audio, target_sr

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    if orig_sr != target_sr:
        num_target_samples = int(len(audio) * float(target_sr) / orig_sr)
        audio = signal.resample(audio, num_target_samples)

    audio = audio - np.mean(audio)

    peak = float(np.max(np.abs(audio)))
    if peak > 0.001:
        scale_factor = target_peak / peak
        scale_factor = min(scale_factor, 6.0)
        audio = audio * scale_factor

    audio = np.clip(audio, -1.0, 1.0).astype(np.float32)
    return audio, target_sr
