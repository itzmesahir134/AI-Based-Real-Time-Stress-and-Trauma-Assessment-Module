import numpy as np
import pytest
from services.audio_worker.vad import detect_voice_activity


@pytest.mark.unit
def test_vad_speech_detection():
    sr = 16000
    # 0.5s silence + 1.0s active speech burst + 0.5s silence
    silence_pre = np.zeros(int(sr * 0.5), dtype=np.float32)
    t = np.linspace(0, 1.0, sr, endpoint=False)
    speech = (0.6 * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
    silence_post = np.zeros(int(sr * 0.5), dtype=np.float32)

    audio = np.concatenate([silence_pre, speech, silence_post])

    segments = detect_voice_activity(audio, sample_rate=sr)
    assert len(segments) >= 1
    # Speech starts near 0.5s and ends near 1.5s
    assert segments[0].start_time >= 0.40
    assert segments[0].end_time <= 1.80
    assert segments[0].confidence > 0.50


@pytest.mark.unit
def test_vad_pure_silence():
    # Only silence
    audio = np.zeros(16000 * 2, dtype=np.float32)
    segments = detect_voice_activity(audio, sample_rate=16000)
    assert len(segments) == 0
