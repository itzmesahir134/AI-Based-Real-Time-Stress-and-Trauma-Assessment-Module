"""M08: Voice Feature Extractor for acoustic and prosodic stress/distress indicators.

Extracts pitch (F0), jitter, shimmer, RMS energy, spectral centroid,
zero-crossing rate, 13 MFCC coefficients, pause dynamics, and syllable speech rate.
Uses pure numpy and scipy signal processing for speed and determinism.
"""

from typing import List, Optional, Union
import numpy as np
from scipy.fft import dct, rfft, rfftfreq

from packages.schemas.audio import SpeechSegment, VoiceFeatureVector


def _hz_to_mel(hz: np.ndarray) -> np.ndarray:
    return 2595.0 * np.log10(1.0 + hz / 700.0)


def _mel_to_hz(mel: np.ndarray) -> np.ndarray:
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def _build_mel_filterbank(n_mels: int, n_fft: int, sample_rate: int) -> np.ndarray:
    """Build triangular Mel filterbank matrix of shape (n_mels, n_fft // 2 + 1)."""
    low_freq_mel = _hz_to_mel(np.array(0.0))
    high_freq_mel = _hz_to_mel(np.array(sample_rate / 2.0))
    mel_points = np.linspace(low_freq_mel, high_freq_mel, n_mels + 2)
    hz_points = _mel_to_hz(mel_points)
    bin_points = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)

    filterbank = np.zeros((n_mels, n_fft // 2 + 1), dtype=np.float32)
    for m in range(1, n_mels + 1):
        f_m_minus = bin_points[m - 1]
        f_m = bin_points[m]
        f_m_plus = bin_points[m + 1]

        for k in range(f_m_minus, f_m):
            if f_m != f_m_minus:
                filterbank[m - 1, k] = (k - f_m_minus) / (f_m - f_m_minus)
        for k in range(f_m, f_m_plus):
            if f_m_plus != f_m:
                filterbank[m - 1, k] = (f_m_plus - k) / (f_m_plus - f_m)

    return filterbank


def extract_voice_features(
    audio: np.ndarray,
    speech_segments: Optional[List[Union[SpeechSegment, dict]]] = None,
    sample_rate: int = 16000,
) -> VoiceFeatureVector:
    """Spec M08: Voice Feature Extractor.

    Args:
        audio: 1D normalized float32 array
        speech_segments: List of SpeechSegment objects or dicts with start_time/end_time
        sample_rate: Audio sampling rate in Hz (default 16000)

    Returns:
        VoiceFeatureVector with prosodic, spectral, and perturbation features.
    """
    if len(audio) == 0:
        return VoiceFeatureVector()

    # Ensure float32 normalized to [-1.0, 1.0]
    if np.issubdtype(audio.dtype, np.integer):
        max_val = np.iinfo(audio.dtype).max
        audio = audio.astype(np.float32) / max_val
    else:
        audio = audio.astype(np.float32)

    total_duration = len(audio) / sample_rate

    # Standardize speech segments
    norm_segments: List[tuple[float, float]] = []
    if speech_segments:
        for seg in speech_segments:
            if isinstance(seg, dict):
                st = float(seg.get("start_time", 0.0))
                et = float(seg.get("end_time", 0.0))
            else:
                st = float(seg.start_time)
                et = float(seg.end_time)
            if et > st:
                norm_segments.append((max(0.0, st), min(total_duration, et)))

    # If no speech segments supplied, treat entire audio as candidate speech
    if not norm_segments:
        norm_segments = [(0.0, total_duration)]

    # Compute pause dynamics
    norm_segments.sort(key=lambda s: s[0])
    pauses: List[float] = []
    prev_end = 0.0
    for st, et in norm_segments:
        gap = st - prev_end
        if gap >= 0.20:  # Pause threshold: >= 200ms
            pauses.append(gap)
        prev_end = max(prev_end, et)
    tail_gap = total_duration - prev_end
    if tail_gap >= 0.20:
        pauses.append(tail_gap)

    pause_count = len(pauses)
    total_pause_duration = sum(pauses)
    pause_ratio = float(np.clip(total_pause_duration / max(total_duration, 1e-4), 0.0, 1.0))

    # Syllable rate estimation over active speech
    total_speech_duration = sum(et - st for st, et in norm_segments)

    # Frame slicing setup
    frame_len = int(sample_rate * 0.030)  # 30 ms
    hop_len = int(sample_rate * 0.015)    # 15 ms
    n_fft = 512
    window = np.hamming(frame_len)
    freqs = rfftfreq(n_fft, 1.0 / sample_rate)
    mel_fb = _build_mel_filterbank(n_mels=26, n_fft=n_fft, sample_rate=sample_rate)

    min_lag = int(sample_rate / 450.0)  # 450 Hz upper pitch limit (~35 samples)
    max_lag = int(sample_rate / 65.0)   # 65 Hz lower pitch limit (~246 samples)

    speech_frames: List[np.ndarray] = []
    for st, et in norm_segments:
        start_idx = int(st * sample_rate)
        end_idx = int(et * sample_rate)
        seg_audio = audio[start_idx:end_idx]
        if len(seg_audio) < frame_len:
            continue
        num_frames = (len(seg_audio) - frame_len) // hop_len + 1
        for i in range(num_frames):
            frame = seg_audio[i * hop_len : i * hop_len + frame_len]
            speech_frames.append(frame)

    if not speech_frames:
        return VoiceFeatureVector(
            pause_ratio=pause_ratio,
            pause_count=pause_count,
            voiced_fraction=0.0,
        )

    # Syllable peak counting using envelope
    syllable_count = 0
    if total_speech_duration >= 0.20:
        frame_energies = [np.sqrt(np.mean(f ** 2)) for f in speech_frames]
        if frame_energies:
            p85 = float(np.percentile(frame_energies, 85))
            min_height = max(p85 * 0.25, 1e-4)
            min_dist = int(0.150 / 0.015)  # min 150ms between syllable peaks (~10 frames)
            # Simple peak picking with local maximum and minimum distance
            last_peak = -min_dist
            for idx in range(1, len(frame_energies) - 1):
                if (
                    frame_energies[idx] > frame_energies[idx - 1]
                    and frame_energies[idx] >= frame_energies[idx + 1]
                    and frame_energies[idx] >= min_height
                    and (idx - last_peak) >= min_dist
                ):
                    syllable_count += 1
                    last_peak = idx

    speech_rate_syl_per_sec = float(np.clip(syllable_count / max(total_speech_duration, 1e-4), 0.0, 12.0))

    # Feature accumulators
    f0_values: List[float] = []
    voiced_amplitudes: List[float] = []
    energies: List[float] = []
    zcrs: List[float] = []
    centroids: List[float] = []
    mfccs: List[np.ndarray] = []

    for frame in speech_frames:
        # RMS energy
        rms = float(np.sqrt(np.mean(frame ** 2)))
        energies.append(rms)

        # Zero crossing rate
        zcr = float(np.mean(np.abs(np.diff(frame >= 0))))
        zcrs.append(zcr)

        # Spectral centroid & MFCC
        w_frame = frame * window
        fft_mag = np.abs(rfft(w_frame, n=n_fft))
        mag_sum = np.sum(fft_mag)
        if mag_sum > 1e-8:
            centroid = float(np.sum(freqs * fft_mag) / mag_sum)
        else:
            centroid = 0.0
        centroids.append(centroid)

        # Mel energies & MFCC (13 coeffs)
        power_spec = (fft_mag ** 2) / n_fft
        mel_energies = np.dot(mel_fb, power_spec)
        log_mel = np.log(np.maximum(mel_energies, 1e-10))
        mfcc_13 = dct(log_mel, type=2, norm="ortho")[:13]
        mfccs.append(mfcc_13)

        # Autocorrelation pitch extraction
        if rms > 1e-3:
            centered = frame - np.mean(frame)
            # Normalized autocorrelation for pitch
            ac = np.correlate(centered, centered, mode="full")
            ac = ac[len(centered) - 1 :]
            norm_factor = ac[0]
            if norm_factor > 1e-8 and len(ac) > max_lag:
                nac = ac / norm_factor
                search_region = nac[min_lag:max_lag]
                peak_idx = int(np.argmax(search_region)) + min_lag
                peak_val = nac[peak_idx]

                if peak_val >= 0.35:
                    f0 = sample_rate / float(peak_idx)
                    f0_values.append(f0)
                    voiced_amplitudes.append(rms)

    # Aggregate pitch features
    if f0_values:
        f0_arr = np.array(f0_values, dtype=np.float32)
        pitch_mean = float(np.mean(f0_arr))
        pitch_std = float(np.std(f0_arr))
        pitch_range = float(np.ptp(f0_arr))
    else:
        pitch_mean = 0.0
        pitch_std = 0.0
        pitch_range = 0.0

    voiced_fraction = float(np.clip(len(f0_values) / max(len(speech_frames), 1), 0.0, 1.0))

    # Jitter (period perturbation): relative mean absolute period difference
    if len(f0_values) >= 2:
        periods = 1.0 / np.array(f0_values, dtype=np.float64)
        mean_period = np.mean(periods)
        if mean_period > 1e-8:
            jitter = float(np.mean(np.abs(np.diff(periods))) / mean_period)
        else:
            jitter = 0.0
    else:
        jitter = 0.0

    # Shimmer (amplitude perturbation): relative mean absolute amplitude difference
    if len(voiced_amplitudes) >= 2:
        amps = np.array(voiced_amplitudes, dtype=np.float64)
        mean_amp = np.mean(amps)
        if mean_amp > 1e-8:
            shimmer = float(np.mean(np.abs(np.diff(amps))) / mean_amp)
        else:
            shimmer = 0.0
    else:
        shimmer = 0.0

    # Energy aggregates
    energy_mean = float(np.mean(energies)) if energies else 0.0
    energy_std = float(np.std(energies)) if energies else 0.0

    # ZCR & Centroid aggregates
    zcr_mean = float(np.mean(zcrs)) if zcrs else 0.0
    spectral_centroid_mean = float(np.mean(centroids)) if centroids else 0.0

    # MFCC aggregates
    if mfccs:
        mfcc_mat = np.array(mfccs)
        mfcc_mean = [round(float(x), 4) for x in np.mean(mfcc_mat, axis=0)]
        mfcc_std = [round(float(x), 4) for x in np.std(mfcc_mat, axis=0)]
    else:
        mfcc_mean = [0.0] * 13
        mfcc_std = [0.0] * 13

    return VoiceFeatureVector(
        pitch_mean=round(pitch_mean, 2),
        pitch_std=round(pitch_std, 2),
        pitch_range=round(pitch_range, 2),
        speech_rate_syl_per_sec=round(speech_rate_syl_per_sec, 2),
        pause_ratio=round(pause_ratio, 3),
        pause_count=pause_count,
        energy_mean=round(energy_mean, 4),
        energy_std=round(energy_std, 4),
        jitter=round(float(np.clip(jitter, 0.0, 1.0)), 4),
        shimmer=round(float(np.clip(shimmer, 0.0, 1.0)), 4),
        mfcc_mean=mfcc_mean,
        mfcc_std=mfcc_std,
        spectral_centroid_mean=round(spectral_centroid_mean, 2),
        zcr_mean=round(zcr_mean, 4),
        voiced_fraction=round(voiced_fraction, 3),
        feature_schema_version="v1.0.0",
    )
