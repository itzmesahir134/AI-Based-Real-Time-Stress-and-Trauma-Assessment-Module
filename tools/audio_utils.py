"""Audio utility functions for standardizing, loading, and inspecting test audio files.

All test samples in curated/ and augmented/ are standardized to:
- Format: WAV
- Channels: 1 (Mono)
- Sample Rate: 16,000 Hz
- Bit Depth: 16-bit PCM (signed integer)
"""

import io
import math
import os
import wave
from typing import Dict, Tuple, Union
import numpy as np
from scipy import signal

try:
    import av
    HAS_AV = True
except ImportError:
    HAS_AV = False


def load_audio(source: Union[str, bytes]) -> Tuple[np.ndarray, int]:
    """Loads audio from a file path or raw bytes.

    Supports standard WAV (via built-in wave module) as well as FLAC/MP3/AAC
    (via PyAV if available). Returns mono float32 array normalized to [-1.0, 1.0]
    and the native sample rate.
    """
    if isinstance(source, str):
        with open(source, "rb") as f:
            raw_bytes = f.read()
    else:
        raw_bytes = source

    # Try standard wave module first
    try:
        with wave.open(io.BytesIO(raw_bytes), "rb") as wf:
            num_channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            n_frames = wf.getnframes()
            data = wf.readframes(n_frames)

            if sample_width == 2:
                audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 4:
                audio = np.frombuffer(data, dtype=np.int32).astype(np.float32) / 2147483648.0
            elif sample_width == 1:
                audio = (np.frombuffer(data, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            else:
                audio = np.frombuffer(data, dtype=np.float32)

            if num_channels > 1:
                audio = audio.reshape(-1, num_channels).mean(axis=1)

            return audio.astype(np.float32), sample_rate
    except wave.Error:
        pass

    # Fallback to PyAV for MP3 / FLAC / container formats
    if HAS_AV:
        bio = io.BytesIO(raw_bytes)
        container = av.open(bio)
        audio_stream = next((s for s in container.streams if s.type == "audio"), None)
        if audio_stream is not None:
            sample_rate = audio_stream.codec_context.sample_rate
            frames = []
            for frame in container.decode(audio_stream):
                arr = frame.to_ndarray()
                if arr.ndim > 1:
                    arr = arr.mean(axis=0)
                frames.append(arr.astype(np.float32))
            if frames:
                audio = np.concatenate(frames)
                if np.issubdtype(audio.dtype, np.integer):
                    max_val = np.iinfo(audio.dtype).max
                    audio = audio.astype(np.float32) / max_val
                elif np.max(np.abs(audio)) > 1.0:
                    audio = audio / np.max(np.abs(audio))
                return audio.astype(np.float32), sample_rate

    # If all else fails, assume raw 16-bit PCM at 16kHz
    audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    return audio.astype(np.float32), 16000


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int = 16000) -> np.ndarray:
    """Resamples a 1D audio numpy array to target_sr using polyphase filtering."""
    if orig_sr == target_sr or len(audio) == 0:
        return audio

    gcd = math.gcd(orig_sr, target_sr)
    up = target_sr // gcd
    down = orig_sr // gcd

    # Use resample_poly for fast polyphase filtering
    resampled = signal.resample_poly(audio, up, down)
    return resampled.astype(np.float32)


def save_wav(file_path: str, audio: np.ndarray, sample_rate: int = 16000) -> None:
    """Saves a 1D float32 audio array as a standard 16-bit Mono WAV file.

    Clips amplitude to [-1.0, 1.0] and writes valid RIFF/WAVE header.
    """
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

    clipped = np.clip(audio, -1.0, 1.0)
    int_pcm = (clipped * 32767.0).astype(np.int16)

    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(int_pcm.tobytes())


def standardize_audio(
    source: Union[str, bytes],
    output_path: str,
    target_sr: int = 16000,
    normalize_peak: bool = True,
    peak_target: float = 0.92,
) -> Dict[str, Union[float, int, str]]:
    """Standardizes input audio into 16kHz Mono 16-bit PCM WAV.

    Returns audio characteristics dictionary.
    """
    audio, orig_sr = load_audio(source)

    # Downsample / resample to target_sr
    if orig_sr != target_sr:
        audio = resample_audio(audio, orig_sr, target_sr)

    # Remove DC bias
    if len(audio) > 0:
        audio = audio - np.mean(audio)

    # Normalize peak if requested
    if normalize_peak and len(audio) > 0:
        current_peak = float(np.max(np.abs(audio)))
        if current_peak > 1e-4:
            scale = peak_target / current_peak
            scale = min(scale, 6.0)  # Avoid blowing up near-silence
            audio = audio * scale

    save_wav(output_path, audio, sample_rate=target_sr)

    stats = analyze_audio_properties(audio, target_sr)
    stats["orig_sample_rate"] = orig_sr
    stats["target_sample_rate"] = target_sr
    stats["output_path"] = output_path
    return stats


def analyze_audio_properties(audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, float]:
    """Analyzes duration, RMS, peak amplitude, estimated SNR, clipping, and silence ratio."""
    if len(audio) == 0:
        return {
            "duration_seconds": 0.0,
            "rms_db": -99.0,
            "peak_amplitude": 0.0,
            "clipping_ratio": 0.0,
            "silence_ratio": 1.0,
            "estimated_snr": 0.0,
        }

    duration = len(audio) / float(sample_rate)
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio**2)))
    rms_db = 20.0 * np.log10(max(rms, 1e-6))

    # Clipping: samples near full digital scale
    clipping_ratio = float(np.mean(np.abs(audio) >= 0.99))

    # Frame-based silence analysis (25ms frames, 10ms hop)
    frame_len = int(sample_rate * 0.025)
    hop_len = int(sample_rate * 0.010)
    if len(audio) >= frame_len:
        num_frames = 1 + (len(audio) - frame_len) // hop_len
        frame_rms = np.array([
            np.sqrt(np.mean(audio[i * hop_len : i * hop_len + frame_len] ** 2))
            for i in range(num_frames)
        ])
        silence_thresh = max(rms * 0.05, 0.005)
        silence_ratio = float(np.mean(frame_rms < silence_thresh))

        noise_floor = np.percentile(frame_rms, 10) + 1e-6
        speech_energy = np.percentile(frame_rms, 90) + 1e-6
        estimated_snr = float(max(0.0, 20.0 * np.log10(speech_energy / noise_floor)))
    else:
        silence_ratio = 1.0 if rms < 0.005 else 0.0
        estimated_snr = 10.0

    return {
        "duration_seconds": round(duration, 3),
        "rms_db": round(rms_db, 1),
        "peak_amplitude": round(peak, 4),
        "clipping_ratio": round(clipping_ratio, 4),
        "silence_ratio": round(silence_ratio, 3),
        "estimated_snr": round(estimated_snr, 1),
    }
