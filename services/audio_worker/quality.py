from typing import List, Tuple
import numpy as np
from packages.schemas import AudioQualityResult


def analyze_audio_quality(
    audio: np.ndarray,
    sample_rate: int = 16000,
    packet_loss: float = 0.0,
) -> AudioQualityResult:
    """Spec M04: Analyzes audio reliability and SNR before downstream acoustic analysis.

    Args:
        audio: 1D numpy array of audio samples (float32 normalized between -1.0 and 1.0)
        sample_rate: Audio sampling rate in Hz (default 16000)
        packet_loss: Known packet loss from WebRTC stats (0.0 to 1.0)

    Returns:
        AudioQualityResult with quality_score, SNR, clipping, and distortion flags.
    """
    if len(audio) == 0:
        return AudioQualityResult(
            quality_score=0.0,
            snr_estimate=0.0,
            clipping_ratio=0.0,
            speech_ratio=0.0,
            packet_loss=packet_loss,
            distortion_flags=["EMPTY_AUDIO"],
        )

    # Ensure float32 normalized to [-1.0, 1.0]
    if np.issubdtype(audio.dtype, np.integer):
        max_val = np.iinfo(audio.dtype).max
        audio = audio.astype(np.float32) / max_val
    else:
        audio = audio.astype(np.float32)

    total_samples = len(audio)
    flags: List[str] = []

    # 1. Check for near-silence / empty signal
    peak_amplitude = float(np.max(np.abs(audio)))
    if peak_amplitude < 0.01:
        flags.append("NEAR_SILENCE")
        return AudioQualityResult(
            quality_score=0.05,
            snr_estimate=0.0,
            clipping_ratio=0.0,
            speech_ratio=0.0,
            packet_loss=packet_loss,
            distortion_flags=flags,
        )

    # 2. Clipping Detection (Spec M04: sample near clipping threshold)
    clipped_samples = np.sum(np.abs(audio) >= 0.99)
    clipping_ratio = float(clipped_samples / total_samples)
    if clipping_ratio > 0.01:
        flags.append("CLIPPING_DETECTED")

    # 3. Zero-Crossing Rate (ZCR) for detecting pure noise/hiss
    zcr = float(np.mean(np.diff(np.signbit(audio)) != 0)) if total_samples > 1 else 0.0
    is_wideband_noise = zcr > 0.35  # White noise has ZCR ~0.50, human voice < 0.20

    # 4. Frame Energy Distribution & SNR
    frame_length = int(sample_rate * 0.02)  # 20ms frames
    hop_length = int(sample_rate * 0.01)    # 10ms hop

    if total_samples < frame_length:
        frame_energies = np.array([np.mean(audio**2)])
    else:
        num_frames = (total_samples - frame_length) // hop_length + 1
        frame_energies = np.array([
            np.mean(audio[i * hop_length : i * hop_length + frame_length] ** 2)
            for i in range(num_frames)
        ])

    sorted_energies = np.sort(frame_energies)
    min_energy = float(np.min(frame_energies))
    max_energy = float(np.max(frame_energies))
    dynamic_range_db = float(10.0 * np.log10(max(max_energy, 1e-9) / max(min_energy, 1e-9)))

    if is_wideband_noise:
        # Wideband random noise floor: signal power is noise power
        snr_db = 4.0
        speech_ratio = 0.05
        flags.append("HIGH_NOISE_FLOOR")
    elif dynamic_range_db < 3.0 and max_energy > 0.002:
        # Harmonic clean steady tone / voiced sound
        reference_ambient_floor = 3.0e-5
        snr_db = float(10.0 * np.log10(max(max_energy, 1e-9) / reference_ambient_floor))
        speech_ratio = 1.0
    else:
        noise_floor_idx = max(1, int(len(sorted_energies) * 0.10))
        noise_floor = float(np.mean(sorted_energies[:noise_floor_idx]))
        signal_idx = max(1, int(len(sorted_energies) * 0.80))
        signal_power = float(np.mean(sorted_energies[signal_idx:]))

        snr_db = float(10.0 * np.log10(max(signal_power, 1e-9) / max(noise_floor, 1e-9)))
        threshold = max(noise_floor * 2.0, 1e-5)
        active_frames = np.sum(frame_energies > threshold)
        speech_ratio = float(active_frames / len(frame_energies))

    snr_db = max(0.0, min(snr_db, 50.0))  # Clamp between 0 and 50 dB

    if snr_db < 10.0 and "HIGH_NOISE_FLOOR" not in flags:
        flags.append("HIGH_NOISE_FLOOR")

    if speech_ratio < 0.10:
        flags.append("LOW_SPEECH_ACTIVITY")

    if packet_loss > 0.08:
        flags.append("NETWORK_PACKET_LOSS")

    # 5. Composite Quality Score Calculation (Spec M04: 0.0 to 1.0)
    snr_score = np.clip((snr_db - 5.0) / 20.0, 0.1, 1.0)
    clipping_penalty = min(0.5, clipping_ratio * 5.0)
    packet_loss_penalty = min(0.4, packet_loss * 2.0)
    noise_penalty = 0.4 if is_wideband_noise else 0.0

    quality_score = float(snr_score - clipping_penalty - packet_loss_penalty - noise_penalty)
    quality_score = float(np.clip(quality_score, 0.05, 1.0))

    return AudioQualityResult(
        quality_score=round(quality_score, 3),
        snr_estimate=round(snr_db, 2),
        clipping_ratio=round(clipping_ratio, 4),
        speech_ratio=round(speech_ratio, 3),
        packet_loss=round(packet_loss, 3) if packet_loss else None,
        distortion_flags=flags,
    )
