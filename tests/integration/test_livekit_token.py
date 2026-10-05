import importlib.util
from pathlib import Path
import pytest
import numpy as np
from httpx import AsyncClient
from services.api.routers.ws_svi import broadcast_svi_update

# Import SaathiRealtimeAgent from apps/realtime-agent/agent.py
agent_path = Path(__file__).resolve().parent.parent.parent / "apps" / "realtime-agent" / "agent.py"
spec = importlib.util.spec_from_file_location("realtime_agent", agent_path)
realtime_agent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(realtime_agent_mod)
SaathiRealtimeAgent = realtime_agent_mod.SaathiRealtimeAgent


@pytest.mark.asyncio
async def test_livekit_token_unconfigured_returns_gracefully(async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    """Without LIVEKIT_API_KEY, endpoint returns fallback token indicator with HTTP 200."""
    from packages.config import Settings, get_settings
    
    settings = get_settings()
    monkeypatch.setattr(settings, "LIVEKIT_API_KEY", None)
    monkeypatch.setattr(settings, "LIVEKIT_API_SECRET", None)

    res = await async_client.get("/api/v1/livekit/token?session_id=test-session-123&identity=caller")
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["token"] == "LIVEKIT_NOT_CONFIGURED"
    assert data["room"] == "test-session-123"
    assert data["identity"] == "caller"
    assert data["url"] is None


@pytest.mark.asyncio
async def test_broadcast_svi_update_no_crash():
    """Verify that broadcasting SVI updates to in-memory listeners does not throw exceptions."""
    payload = {
        "session_id": "test-session-123",
        "svi": 55.4,
        "risk_band": "HIGH",
        "confidence": 0.85,
        "partial": True,
    }
    # Should complete without error even if Redis is unavailable
    await broadcast_svi_update("test-session-123", payload)


@pytest.mark.asyncio
async def test_realtime_agent_process_audio_chunk():
    """Verify realtime agent buffers and processes 3s PCM audio chunks."""
    agent = SaathiRealtimeAgent(room_name="test-room-456", chunk_duration_sec=1.0)
    await agent.start()
    assert agent.is_running is True

    # 1 second of 16kHz audio (16000 samples = 32000 bytes int16)
    t = np.linspace(0, 1.0, 16000, endpoint=False)
    # 440Hz sine wave (voiced signal)
    pcm_data = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16).tobytes()

    res = await agent.process_audio_chunk(pcm_data, sample_rate=16000)
    assert res is not None
    assert "partial" in res
    assert res["partial"] is True
    assert "session_id" in res
    assert res["session_id"] == "test-room-456"

    # Test feed_frame buffer mechanism
    await agent.feed_frame(pcm_data)
    assert agent.chunk_index >= 1

    await agent.stop()
    assert agent.is_running is False
