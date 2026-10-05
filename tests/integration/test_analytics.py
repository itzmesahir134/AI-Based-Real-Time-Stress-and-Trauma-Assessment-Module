"""Integration tests for the analytics summary endpoint (Phase 13B)."""
import uuid
import pytest
from httpx import AsyncClient
from services.api.db import SessionModel, CaseModel, SVIResultModel


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analytics_summary_empty_db(async_client: AsyncClient):
    """Analytics returns zero-counts gracefully on empty DB."""
    # Login as supervisor
    login = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "supervisor", "password": "saathi-super-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]

    res = await async_client.get(
        "/api/v1/analytics/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_sessions" in data
    assert "total_cases" in data
    assert "risk_band_distribution" in data
    assert "avg_svi" in data
    assert "abstention_rate" in data
    assert "cases_last_24h" in data
    assert data["total_sessions"] == 0
    assert data["total_cases"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analytics_summary_populated_db(async_client: AsyncClient, db_session):
    """Analytics returns correct counts when DB has data."""
    # Login as supervisor
    login = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "supervisor", "password": "saathi-super-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]

    # Seed data
    s1 = SessionModel(id=uuid.uuid4(), channel="WEB_AUDIO")
    db_session.add(s1)
    await db_session.flush()

    c1 = CaseModel(id=uuid.uuid4(), session_id=s1.id, priority="HIGH", status="OPEN")
    c2 = CaseModel(id=uuid.uuid4(), session_id=s1.id, priority="CRITICAL", status="IN_REVIEW")
    db_session.add_all([c1, c2])
    await db_session.commit()

    res = await async_client.get(
        "/api/v1/analytics/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_sessions"] == 1
    assert data["total_cases"] == 2
    assert "HIGH" in data["risk_band_distribution"]
    assert data["risk_band_distribution"]["HIGH"] == 1
    assert data["cases_in_review"] == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analytics_requires_supervisor_role(async_client: AsyncClient):
    """RESPONDER should not be able to access analytics (403)."""
    login = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "responder", "password": "saathi-resp-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]

    res = await async_client.get(
        "/api/v1/analytics/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
