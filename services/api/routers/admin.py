"""Admin endpoints: audit log viewer + model version registry (Phase 13C)."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.db import get_db, AuditLogModel
from services.api.security import require_role

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

# Hard-coded model version registry for SIH prototype.
# In production this would come from the model_versions DB table.
MODEL_REGISTRY: List[Dict[str, str]] = [
    {"module": "audio_quality",   "version": "v1.0.0-snr-heuristic",      "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "vad",             "version": "v1.0.0-energy-threshold",   "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "transcriber",     "version": "v1.0.0-whisper-stub",       "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "voice_features",  "version": "v1.0.0-librosa-heuristic",  "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "voice_model",     "version": "v1.0.0-pitch-rate-heuristic", "status": "ACTIVE", "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "text_normalizer", "version": "v1.0.0-regex",              "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "text_model",      "version": "v1.0.0-lexicon-heuristic",  "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "crisis_detector", "version": "v1.0.0-keyword-rules",     "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "self_report",     "version": "v1.0.0-weighted-sum",       "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "context_scorer",  "version": "v1.0.0-weighted-sum",       "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "svi_engine",      "version": "v1.0.0-qcw-fusion",        "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
    {"module": "recommendations", "version": "v1.0.0-rule-template",     "status": "ACTIVE",  "deployed_at": "2026-10-01T00:00:00Z"},
]


@router.get(
    "/model-versions",
    dependencies=[Depends(require_role("ADMIN", "AUDITOR"))],
)
async def get_model_versions() -> List[Dict[str, str]]:
    """Phase 13C: Returns the registered model version table."""
    return MODEL_REGISTRY


@router.get(
    "/audit-log",
    dependencies=[Depends(require_role("ADMIN", "AUDITOR"))],
)
async def get_audit_log(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=200, description="Results per page"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Phase 13C: Returns paginated audit log entries, newest first."""
    offset = (page - 1) * limit

    query = select(AuditLogModel).order_by(AuditLogModel.timestamp.desc())
    if action:
        query = query.where(AuditLogModel.action == action)

    count_query = select(AuditLogModel)
    if action:
        count_query = count_query.where(AuditLogModel.action == action)

    from sqlalchemy import func
    total = (await db.execute(
        select(func.count()).select_from(count_query.subquery())
    )).scalar() or 0

    result = await db.execute(query.offset(offset).limit(limit))
    rows = result.scalars().all()

    entries = [
        {
            "id": str(row.id),
            "user_id": row.user_id,
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "details": row.details,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        }
        for row in rows
    ]

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "entries": entries,
    }
