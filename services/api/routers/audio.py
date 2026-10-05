from typing import Optional
import uuid
import io
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from packages.schemas import AudioQualityResult, TranscriptResponse, VoiceFeatureVector
from packages.config import get_settings
from packages.utils import get_logger
from services.audio_worker import (
    Transcriber,
    analyze_audio_quality,
    bytes_to_pcm_array,
    detect_voice_activity,
    extract_voice_features,
    preprocess_audio,
)

router = APIRouter(prefix="/api/v1/audio", tags=["Audio Pipeline"])
transcriber = Transcriber()
logger = get_logger("saathi.api.audio")


async def upload_to_minio(session_id: str, audio_bytes: bytes) -> Optional[str]:
    """Phase 13D: Upload raw audio bytes to MinIO. Returns object key or None on failure."""
    try:
        from minio import Minio
        import asyncio
        settings = get_settings()
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        key = f"{session_id}/{uuid.uuid4()}.wav"
        buf = io.BytesIO(audio_bytes)
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.put_object(
                settings.MINIO_BUCKET_AUDIO,
                key,
                buf,
                length=len(audio_bytes),
                content_type="audio/wav",
            ),
        )
        logger.info("audio_uploaded_to_minio", key=key, bytes=len(audio_bytes))
        return key
    except ImportError:
        logger.warning("minio_sdk_not_installed", session_id=session_id)
        return None
    except Exception as e:
        logger.warning("minio_upload_failed", session_id=session_id, error=str(e))
        return None


@router.post("/quality", response_model=AudioQualityResult, status_code=status.HTTP_200_OK)
async def check_audio_quality(
    file: UploadFile = File(..., description="Audio file payload (WAV or PCM binary)"),
    packet_loss: float = Query(0.0, ge=0.0, le=1.0, description="WebRTC packet loss ratio"),
):
    """Spec M04: Analyzes audio quality, SNR, and clipping ratio before inference."""
    try:
        content = await file.read()
        audio, sample_rate = bytes_to_pcm_array(content)
        quality = analyze_audio_quality(audio, sample_rate=sample_rate, packet_loss=packet_loss)
        return quality
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process audio quality: {str(e)}",
        )


@router.post("/transcribe", response_model=TranscriptResponse, status_code=status.HTTP_200_OK)
async def transcribe_speech(
    file: UploadFile = File(..., description="Audio file payload (WAV or PCM)"),
    language: Optional[str] = Query(None, description="Target language code (e.g. 'hi', 'en', 'ta')"),
    session_id: Optional[str] = Query(None, description="Session ID for MinIO storage key"),
):
    """Spec M07: Converts speech to timestamped transcript with integrated quality check.
    Phase 13D: If session_id provided, uploads raw audio to MinIO before transcribing.
    """
    try:
        content = await file.read()
        if session_id:
            await upload_to_minio(session_id, content)
        audio, sample_rate = bytes_to_pcm_array(content)
        cleaned_audio, sr = preprocess_audio(audio, orig_sr=sample_rate)
        result = transcriber.transcribe(cleaned_audio, sample_rate=sr, language=language)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to transcribe speech: {str(e)}",
        )


@router.post("/features", response_model=VoiceFeatureVector, status_code=status.HTTP_200_OK)
async def extract_audio_features(
    file: UploadFile = File(..., description="Audio file payload (WAV or PCM binary)"),
):
    """Spec M08: Extracts acoustic and prosodic feature vector from audio."""
    try:
        content = await file.read()
        audio, sample_rate = bytes_to_pcm_array(content)
        cleaned_audio, sr = preprocess_audio(audio, orig_sr=sample_rate)
        segments = detect_voice_activity(cleaned_audio, sample_rate=sr)
        features = extract_voice_features(cleaned_audio, speech_segments=segments, sample_rate=sr)
        return features
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract voice features: {str(e)}",
        )
