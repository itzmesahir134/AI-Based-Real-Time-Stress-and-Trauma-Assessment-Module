from .audio import router as audio_router
from .cases import router as cases_router
from .consent import router as consent_router
from .context import router as context_router
from .health import router as health_router
from .inference import router as inference_router
from .recommendations import router as recommendations_router
from .self_report import router as self_report_router
from .sessions import router as sessions_router
from .svi import router as svi_router
from .assessment import router as assessment_router
from .review import router as review_router
from .livekit_token import router as livekit_token_router
from .ws_svi import router as ws_svi_router
from .auth import router as auth_router

__all__ = [
    "auth_router",
    "health_router",
    "sessions_router",
    "consent_router",
    "cases_router",
    "audio_router",
    "inference_router",
    "self_report_router",
    "context_router",
    "svi_router",
    "recommendations_router",
    "assessment_router",
    "review_router",
    "livekit_token_router",
    "ws_svi_router",
]
