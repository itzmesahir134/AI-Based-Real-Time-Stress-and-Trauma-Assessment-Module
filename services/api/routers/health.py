"""Health and readiness probes (Phase 13E enhanced)."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.db import get_db
from packages.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Liveness probe endpoint."""
    return {
        "status": "healthy",
        "service": "saathi-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Phase 13E: Deep readiness probe — checks DB, Redis, MinIO connectivity."""
    checks = {}

    # --- Database ping ---
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"ok": True, "latency_ms": None}
    except Exception as e:
        checks["database"] = {"ok": False, "error": str(e)}

    # --- Redis ping (graceful if not configured) ---
    try:
        import redis.asyncio as aioredis
        settings = get_settings()
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        await r.ping()
        await r.aclose()
        checks["redis"] = {"ok": True}
    except ImportError:
        checks["redis"] = {"ok": True, "note": "redis-py not installed — skipped"}
    except Exception as e:
        checks["redis"] = {"ok": False, "error": str(e)}

    # --- MinIO ping (graceful if not reachable) ---
    try:
        import asyncio
        from minio import Minio
        settings = get_settings()
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: client.list_buckets()
        )
        checks["minio"] = {"ok": True}
    except ImportError:
        checks["minio"] = {"ok": True, "note": "minio SDK not installed — skipped"}
    except Exception as e:
        checks["minio"] = {"ok": False, "error": str(e)}

    healthy = all(v["ok"] for v in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "ready": healthy,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        },
    )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check_legacy(db: AsyncSession = Depends(get_db)):
    """Legacy readiness probe — DB only (kept for backward compatibility)."""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database": f"error: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
