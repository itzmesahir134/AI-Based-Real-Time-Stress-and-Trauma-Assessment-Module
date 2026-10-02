import numpy as np
import pytest
from services.audio_worker.quality import analyze_audio_quality


@pytest.mark.unit
def test_clean_audio_quality():
    # 1 second of 440Hz sine wave (clean audio)
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)

    result = analyze_audio_quality(audio, sample_rate=sr)
    assert result.quality_score >= 0.80
    assert result.snr_estimate is not None and result.snr_estimate >= 20.0
    assert result.clipping_ratio == 0.0
    assert "CLIPPING_DETECTED" not in result.distortion_flags


@pytest.mark.unit
def test_clipped_audio_quality():
    # Saturated / clipped sine wave
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    audio = 2.0 * np.sin(2 * np.pi * 440 * t)
    audio = np.clip(audio, -1.0, 1.0)

    result = analyze_audio_quality(audio, sample_rate=sr)
    assert result.clipping_ratio > 0.05
    assert "CLIPPING_DETECTED" in result.distortion_flags
    # Score should be penalized due to heavy clipping
    assert result.quality_score < 0.95


@pytest.mark.unit
def test_silent_audio_quality():
    # Near silence
    audio = np.zeros(16000, dtype=np.float32)

    result = analyze_audio_quality(audio, sample_rate=16000)
    assert "NEAR_SILENCE" in result.distortion_flags
    assert result.quality_score <= 0.10


@pytest.mark.unit
def test_noisy_audio_quality():
    # Pure white noise
    np.random.seed(42)
    audio = np.random.uniform(-0.5, 0.5, 16000).astype(np.float32)

    result = analyze_audio_quality(audio, sample_rate=16000)
    assert result.snr_estimate is not None
    assert result.snr_estimate < 12.0
