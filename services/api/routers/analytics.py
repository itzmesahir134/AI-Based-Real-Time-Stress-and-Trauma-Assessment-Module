"""Analytics summary endpoint for Phase 13B."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.db import (
    get_db,
    CaseModel,
    SessionModel,
    SVIResultModel,
    VoiceInferenceModel,
)
from services.api.security import require_role

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get(
    "/summary",
    dependencies=[Depends(require_role("SUPERVISOR", "ADMIN"))],
)
async def get_analytics_summary(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Phase 13B: Returns aggregated metrics for the analytics dashboard."""

    # -- Totals --
    total_sessions = (await db.execute(select(func.count()).select_from(SessionModel))).scalar() or 0
    total_cases = (await db.execute(select(func.count()).select_from(CaseModel))).scalar() or 0

    # -- Risk band distribution --
    band_rows = (
        await db.execute(
            select(CaseModel.priority, func.count().label("cnt"))
            .group_by(CaseModel.priority)
        )
    ).all()
    risk_band_distribution: Dict[str, int] = {row.priority: row.cnt for row in band_rows}

    # -- SVI stats --
    svi_stats_row = (
        await db.execute(
            select(
                func.avg(SVIResultModel.svi).label("avg_svi"),
                func.avg(SVIResultModel.confidence).label("avg_confidence"),
                func.avg(SVIResultModel.evidence_coverage).label("avg_evidence_coverage"),
                func.count().label("total_svi"),
            )
        )
    ).one()

    total_svi = svi_stats_row.total_svi or 0
    avg_svi = round(float(svi_stats_row.avg_svi or 0), 2)
    avg_confidence = round(float(svi_stats_row.avg_confidence or 0), 3)
    avg_evidence_coverage = round(float(svi_stats_row.avg_evidence_coverage or 0), 3)

    # Count safety overrides separately to avoid CAST(None) issues
    safety_override_count = (
        await db.execute(
            select(func.count()).select_from(SVIResultModel).where(SVIResultModel.safety_override == True)  # noqa
        )
    ).scalar() or 0

    # -- Abstention rate (voice modality abstained) --
    total_voice = (await db.execute(select(func.count()).select_from(VoiceInferenceModel))).scalar() or 0
    abstained_voice = (
        await db.execute(
            select(func.count()).select_from(VoiceInferenceModel).where(VoiceInferenceModel.abstained == True)  # noqa
        )
    ).scalar() or 0
    abstention_rate = round(abstained_voice / total_voice, 3) if total_voice > 0 else 0.0

    # -- Cases last 24h --
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    cases_last_24h = (
        await db.execute(
            select(func.count()).select_from(CaseModel).where(CaseModel.created_at >= cutoff)
        )
    ).scalar() or 0

    # -- Cases in review --
    cases_in_review = (
        await db.execute(
            select(func.count()).select_from(CaseModel).where(CaseModel.status == "IN_REVIEW")
        )
    ).scalar() or 0

    return {
        "total_sessions": total_sessions,
        "total_cases": total_cases,
        "risk_band_distribution": risk_band_distribution,
        "safety_override_count": safety_override_count,
        "avg_svi": avg_svi,
        "avg_confidence": avg_confidence,
        "avg_evidence_coverage": avg_evidence_coverage,
        "abstention_rate": abstention_rate,
        "cases_last_24h": cases_last_24h,
        "cases_in_review": cases_in_review,
    }
