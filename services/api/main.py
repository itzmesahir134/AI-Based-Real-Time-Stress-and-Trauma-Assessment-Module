from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from packages.config import get_settings
from packages.utils import get_logger, setup_logging
from services.api.db import init_db
from services.api.routers import (
    audio_router,
    cases_router,
    consent_router,
    context_router,
    health_router,
    inference_router,
    recommendations_router,
    self_report_router,
    sessions_router,
    svi_router,
    assessment_router,
    review_router,
    livekit_token_router,
    ws_svi_router,
    auth_router,
)

settings = get_settings()
logger = get_logger("saathi.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events: sets up logging and initializes DB tables (SQLite fallback)."""
    setup_logging(log_level=settings.LOG_LEVEL)
    logger.info("saathi_api_startup", environment=settings.ENVIRONMENT)
    try:
        if settings.DATABASE_URL.startswith("sqlite"):
            await init_db()
            logger.info("database_initialized", engine="sqlite")
        else:
            logger.info("database_managed_by_alembic", engine="postgresql")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
    yield
    logger.info("saathi_api_shutdown")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="SAATHI-AI API",
        description="Multimodal Real-Time Stress & Trauma Assessment System",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler for unhandled exceptions
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error occurred"},
        )

    # Include routers
    app.include_router(health_router)
    app.include_router(sessions_router)
    app.include_router(consent_router)
    app.include_router(cases_router)
    app.include_router(audio_router)
    app.include_router(inference_router)
    app.include_router(self_report_router)
    app.include_router(context_router)
    app.include_router(svi_router)
    app.include_router(recommendations_router)
    app.include_router(assessment_router)
    app.include_router(review_router)
    app.include_router(livekit_token_router)
    app.include_router(ws_svi_router)
    app.include_router(auth_router)

    return app



app = create_app()
