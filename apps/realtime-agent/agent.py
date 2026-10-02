import asyncio
from typing import Optional
from packages.config import get_settings
from packages.utils import get_logger
from services.audio_worker import Transcriber, analyze_audio_quality, preprocess_audio

settings = get_settings()
logger = get_logger("saathi.realtime_agent")


class SaathiRealtimeAgent:
    """Spec §0 & §5.6: LiveKit WebRTC Voice Agent Bridge.
    Connects to live room sessions, receives audio streams, and runs real-time triage.
    """

    def __init__(self, room_name: str, participant_identity: str = "saathi-agent"):
        self.room_name = room_name
        self.participant_identity = participant_identity
        self.transcriber = Transcriber(model_size="base")
        self.is_running = False

    async def start(self):
        """Starts the realtime listener session."""
        logger.info(
            "starting_realtime_agent",
            room=self.room_name,
            livekit_url=settings.LIVEKIT_URL or "ws://localhost:7880",
        )
        self.is_running = True

        # If livekit SDK is configured, connect; otherwise provide mock streaming session for tests
        try:
            from livekit import rtc
            # LiveKit connection flow
            room = rtc.Room()
            # Token generation would happen here using LIVEKIT_API_KEY and LIVEKIT_API_SECRET
            logger.info("livekit_room_initialized", room=self.room_name)
        except ImportError:
            logger.info("livekit_sdk_not_loaded_running_mock_listener", room=self.room_name)

    async def process_audio_chunk(self, chunk_bytes: bytes, sample_rate: int = 16000):
        """Processes an incoming audio frame from the WebRTC track."""
        import numpy as np

        audio = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        cleaned, sr = preprocess_audio(audio, orig_sr=sample_rate)
        quality = analyze_audio_quality(cleaned, sample_rate=sr)
        return quality

    async def stop(self):
        """Stops the realtime listener session."""
        self.is_running = False
        logger.info("realtime_agent_stopped", room=self.room_name)


if __name__ == "__main__":
    agent = SaathiRealtimeAgent(room_name="saathi-triage-demo")
    asyncio.run(agent.start())
