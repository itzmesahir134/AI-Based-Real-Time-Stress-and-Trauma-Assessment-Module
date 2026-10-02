from typing import Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from packages.schemas import AudioQualityResult, TranscriptResponse
from services.audio_worker import (
    Transcriber,
    analyze_audio_quality,
    bytes_to_pcm_array,
    preprocess_audio,
)

router = APIRouter(prefix="/api/v1/audio", tags=["Audio Pipeline"])
transcriber = Transcriber()


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
):
    """Spec M07: Converts speech to timestamped transcript with integrated quality check."""
    try:
        content = await file.read()
        audio, sample_rate = bytes_to_pcm_array(content)
        cleaned_audio, sr = preprocess_audio(audio, orig_sr=sample_rate)
        result = transcriber.transcribe(cleaned_audio, sample_rate=sr, language=language)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to transcribe speech: {str(e)}",
        )
