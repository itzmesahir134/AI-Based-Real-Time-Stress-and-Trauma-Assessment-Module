"""LiveKit WebRTC token generation endpoint with graceful fallback."""

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

from packages.config import get_settings
from packages.utils import get_logger

logger = get_logger("saathi.api.livekit_token")
router = APIRouter(prefix="/api/v1/livekit", tags=["LiveKit"])


class LiveKitTokenResponse(BaseModel):
    token: str
    url: Optional[str] = None
    room: str
    identity: str


@router.get("/token", response_model=LiveKitTokenResponse)
async def get_livekit_token(
    session_id: str = Query(..., description="Session/Room ID"),
    identity: str = Query("caller", description="Participant identity"),
) -> LiveKitTokenResponse:
    """Generates a signed LiveKit WebRTC room token.
    Falls back gracefully if LiveKit credentials are not configured or SDK is unavailable.
    """
    settings = get_settings()

    if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
        logger.info(
            "livekit_not_configured_fallback",
            session_id=session_id,
            identity=identity,
        )
        return LiveKitTokenResponse(
            token="LIVEKIT_NOT_CONFIGURED",
            url=None,
            room=session_id,
            identity=identity,
        )

    try:
        from livekit.api import AccessToken, VideoGrants  # type: ignore

        token = (
            AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(identity)
            .with_name(f"saathi-{identity}")
            .with_grants(VideoGrants(room_join=True, room=session_id))
        )
        jwt_token = token.to_jwt()
        livekit_url = settings.LIVEKIT_URL or "ws://localhost:7880"

        logger.info(
            "livekit_token_generated",
            session_id=session_id,
            identity=identity,
            url=livekit_url,
        )
        return LiveKitTokenResponse(
            token=jwt_token,
            url=livekit_url,
            room=session_id,
            identity=identity,
        )
    except Exception as e:
        logger.warning(
            "livekit_token_generation_failed",
            session_id=session_id,
            error=str(e),
        )
        return LiveKitTokenResponse(
            token="LIVEKIT_NOT_CONFIGURED",
            url=None,
            room=session_id,
            identity=identity,
        )
