import io
import wave
import numpy as np
import pytest
from httpx import AsyncClient


def create_test_wav_bytes(duration: float = 1.0, sr: int = 16000) -> bytes:
    """Helper creating valid in-memory PCM WAV bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        samples = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


@pytest.mark.integration
async def test_audio_quality_endpoint(async_client: AsyncClient):
    wav_bytes = create_test_wav_bytes(duration=1.0)
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}

    res = await async_client.post("/api/v1/audio/quality", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "quality_score" in data
    assert data["quality_score"] > 0.5
    assert "snr_estimate" in data
    assert "distortion_flags" in data


@pytest.mark.integration
async def test_audio_transcribe_endpoint(async_client: AsyncClient):
    wav_bytes = create_test_wav_bytes(duration=1.5)
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}

    res = await async_client.post("/api/v1/audio/transcribe?language=hi", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "segments" in data
    assert "full_text" in data
    assert "quality" in data
    assert data["language"] == "hi"
    assert data["duration_seconds"] > 0.0
