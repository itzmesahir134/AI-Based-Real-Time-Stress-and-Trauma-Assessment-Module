import numpy as np
import pytest
from packages.schemas.audio import SpeechSegment, VoiceFeatureVector
from services.audio_worker.features import extract_voice_features


@pytest.mark.unit
def test_voice_features_tonal_speech():
    sr = 16000
    duration = 1.5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 220 Hz harmonic signal (A3)
    tone = (
        0.5 * np.sin(2 * np.pi * 220 * t)
        + 0.25 * np.sin(2 * np.pi * 440 * t)
        + 0.1 * np.sin(2 * np.pi * 660 * t)
    ).astype(np.float32)

    segments = [SpeechSegment(start_time=0.1, end_time=1.4, confidence=0.9)]
    features = extract_voice_features(tone, speech_segments=segments, sample_rate=sr)

    assert isinstance(features, VoiceFeatureVector)
    assert features.voiced_fraction > 0.7
    # Pitch should detect around 220 Hz (+- 15 Hz)
    assert 200.0 <= features.pitch_mean <= 240.0
    assert len(features.mfcc_mean) == 13
    assert len(features.mfcc_std) == 13
    assert features.energy_mean > 0.01
    assert features.spectral_centroid_mean > 0.0


@pytest.mark.unit
def test_voice_features_pure_silence():
    sr = 16000
    silence = np.zeros(sr * 2, dtype=np.float32)
    features = extract_voice_features(silence, speech_segments=[], sample_rate=sr)

    assert isinstance(features, VoiceFeatureVector)
    assert features.voiced_fraction == 0.0
    assert features.pitch_mean == 0.0
    assert features.pitch_std == 0.0
    assert features.energy_mean == 0.0


@pytest.mark.unit
def test_voice_features_pauses_and_speech_rate():
    sr = 16000
    # 3.0s total: [0.2s pause][0.8s speech][0.5s pause][1.0s speech][0.5s pause]
    t = np.linspace(0, 3.0, sr * 3, endpoint=False)
    audio = np.zeros_like(t, dtype=np.float32)

    # Fill speech bursts with 180Hz signal
    speech_1 = (0.5 * np.sin(2 * np.pi * 180 * t[: int(0.8 * sr)])).astype(np.float32)
    speech_2 = (0.5 * np.sin(2 * np.pi * 180 * t[: int(1.0 * sr)])).astype(np.float32)

    audio[int(0.2 * sr) : int(1.0 * sr)] = speech_1
    audio[int(1.5 * sr) : int(2.5 * sr)] = speech_2

    segments = [
        SpeechSegment(start_time=0.2, end_time=1.0, confidence=0.95),
        SpeechSegment(start_time=1.5, end_time=2.5, confidence=0.95),
    ]

    features = extract_voice_features(audio, speech_segments=segments, sample_rate=sr)

    assert features.pause_count >= 2
    assert features.pause_ratio > 0.25
    assert features.voiced_fraction > 0.30
