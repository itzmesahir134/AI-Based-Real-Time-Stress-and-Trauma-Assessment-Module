"""Spec §0 & §5.6: LiveKit WebRTC Voice Agent Bridge.
Connects to live room sessions, receives audio streams, buffers into 3-second chunks,
and runs real-time acoustic assessment, broadcasting provisional SVI updates to responders.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict
import numpy as np

from packages.config import get_settings
from packages.schemas import ModalityScores, QualityFactors
from packages.utils import get_logger
from services.audio_worker import (
    analyze_audio_quality,
    detect_voice_activity,
    extract_voice_features,
    preprocess_audio,
)
from services.inference import evaluate_voice_distress
from services.scoring import calculate_svi, classify_risk_band
from services.api.routers.ws_svi import broadcast_svi_update

settings = get_settings()
logger = get_logger("saathi.realtime_agent")


class SaathiRealtimeAgent:
    """LiveKit WebRTC Agent for Real-Time Streaming Audio Triage."""

    def __init__(
        self,
        room_name: str,
        participant_identity: str = "saathi-agent",
        target_sample_rate: int = 16000,
        chunk_duration_sec: float = 3.0,
    ):
        self.room_name = room_name
        self.participant_identity = participant_identity
        self.target_sample_rate = target_sample_rate
        self.chunk_duration_sec = chunk_duration_sec
        # 16-bit mono PCM = 2 bytes per sample
        self.chunk_size_bytes = int(target_sample_rate * 2 * chunk_duration_sec)
        self.buffer = bytearray()
        self.chunk_index = 0
        self.is_running = False
        self._room = None

    async def start(self):
        """Starts the realtime listener session and subscribes to room tracks."""
        logger.info(
            "starting_realtime_agent",
            room=self.room_name,
            identity=self.participant_identity,
            livekit_url=settings.LIVEKIT_URL or "ws://localhost:7880",
        )
        self.is_running = True

        if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
            logger.info(
                "livekit_not_configured_running_standalone_mode",
                room=self.room_name,
            )
            return

        try:
            from livekit import rtc
            from livekit.api import AccessToken, VideoGrants

            token = (
                AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
                .with_identity(self.participant_identity)
                .with_name(f"saathi-{self.participant_identity}")
                .with_grants(VideoGrants(room_join=True, room=self.room_name))
            )
            jwt_token = token.to_jwt()
            livekit_url = settings.LIVEKIT_URL or "ws://localhost:7880"

            self._room = rtc.Room()

            @self._room.on("track_subscribed")
            def on_track_subscribed(track, publication, participant):
                if track.kind == rtc.TrackKind.KIND_AUDIO:
                    logger.info("audio_track_subscribed", participant=participant.identity)
                    asyncio.create_task(self._read_audio_stream(rtc.AudioStream(track)))

            await self._room.connect(livekit_url, jwt_token)
            logger.info("connected_to_livekit_room", room=self.room_name)
        except ImportError:
            logger.info("livekit_sdk_not_loaded_running_standalone", room=self.room_name)
        except Exception as e:
            logger.warning("livekit_connection_failed", room=self.room_name, error=str(e))

    async def _read_audio_stream(self, audio_stream):
        """Reads WebRTC audio frames and passes them to chunk buffer."""
        try:
            async for frame_event in audio_stream:
                if not self.is_running:
                    break
                frame_bytes = frame_event.frame.data.tobytes()
                await self.feed_frame(frame_bytes)
        except Exception as e:
            logger.error("audio_stream_reading_error", error=str(e))

    async def feed_frame(self, frame_bytes: bytes):
        """Appends audio bytes to buffer and triggers chunk processing when full."""
        self.buffer.extend(frame_bytes)
        while len(self.buffer) >= self.chunk_size_bytes:
            chunk = bytes(self.buffer[: self.chunk_size_bytes])
            del self.buffer[: self.chunk_size_bytes]
            self.chunk_index += 1
            await self.process_audio_chunk(chunk, sample_rate=self.target_sample_rate)

    async def process_audio_chunk(
        self,
        chunk_bytes: bytes,
        sample_rate: int = 16000,
    ) -> Dict[str, Any]:
        """Processes a 3-second audio chunk through the acoustic distress pipeline."""
        try:
            audio = np.frombuffer(chunk_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            if len(audio) == 0:
                return {"status": "empty"}

            cleaned, sr = preprocess_audio(audio, orig_sr=sample_rate)
            quality = analyze_audio_quality(cleaned, sample_rate=sr)

            # Quality gate: if quality is below threshold, send partial update
            if quality.quality_score < 0.15:
                payload = {
                    "session_id": self.room_name,
                    "svi": None,
                    "risk_band": "LOW",
                    "confidence": 0.0,
                    "evidence_coverage": 0.0,
                    "partial": True,
                    "reason": "poor_audio",
                    "quality_score": round(float(quality.quality_score), 2),
                    "chunk_index": self.chunk_index,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await self.publish_svi(payload)
                return payload

            segments = detect_voice_activity(cleaned, sample_rate=sr)
            features = extract_voice_features(
                cleaned, speech_segments=segments, sample_rate=sr
            )
            voice_distress = evaluate_voice_distress(features, quality=quality)

            voice_score = (
                float(voice_distress.score)
                if (not voice_distress.abstained and voice_distress.score is not None)
                else None
            )

            modality_scores = ModalityScores(voice=voice_score)
            quality_factors = QualityFactors(voice=float(quality.quality_score))
            (
                svi_val,
                confidence,
                evidence_coverage,
                status,
                contributions,
                contributors,
                missing,
            ) = calculate_svi(
                modality_scores=modality_scores,
                quality_factors=quality_factors,
            )
            risk_band = classify_risk_band(svi_val)

            payload = {
                "session_id": self.room_name,
                "svi": round(float(svi_val), 1),
                "risk_band": risk_band.value if hasattr(risk_band, "value") else str(risk_band),
                "confidence": round(float(confidence), 2),
                "evidence_coverage": round(float(evidence_coverage), 2),
                "partial": True,
                "chunk_index": self.chunk_index,
                "voice_score": round(voice_score, 1) if voice_score is not None else None,
                "quality_score": round(float(quality.quality_score), 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self.publish_svi(payload)
            return payload
        except Exception as e:
            logger.error("process_audio_chunk_failed", chunk_index=self.chunk_index, error=str(e))
            return {"status": "error", "error": str(e)}

    async def publish_svi(self, payload: Dict[str, Any]):
        """Broadcasts provisional SVI update to all listeners."""
        await broadcast_svi_update(self.room_name, payload)

    async def stop(self):
        """Stops the realtime listener session and disconnects room."""
        self.is_running = False
        self.buffer.clear()
        if self._room is not None:
            try:
                await self._room.disconnect()
            except Exception:
                pass
            self._room = None
        logger.info("realtime_agent_stopped", room=self.room_name)


if __name__ == "__main__":
    agent = SaathiRealtimeAgent(room_name="saathi-triage-demo")
    asyncio.run(agent.start())
