"""Integration tests for admin endpoints — audit log + model versions (Phase 13C)."""
import uuid
import pytest
from httpx import AsyncClient
from services.api.db import AuditLogModel


@pytest.mark.asyncio
@pytest.mark.integration
async def test_model_versions_admin_access(async_client: AsyncClient):
    """ADMIN can read model version registry."""
    login = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "saathi-admin-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]

    res = await async_client.get(
        "/api/v1/admin/model-versions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "module" in data[0]
    assert "version" in data[0]
    assert "status" in data[0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_model_versions_responder_forbidden(async_client: AsyncClient):
    """RESPONDER cannot access admin endpoints (403)."""
    login = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "responder", "password": "saathi-resp-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]

    res = await async_client.get(
        "/api/v1/admin/model-versions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_audit_log_pagination(async_client: AsyncClient, db_session):
    """Audit log returns paginated results with correct structure."""
    # Seed some audit entries
    for i in range(5):
        db_session.add(AuditLogModel(
            id=uuid.uuid4(),
            user_id="admin",
            action=f"TEST_ACTION_{i}",
            resource_type="CASE",
            resource_id=str(uuid.uuid4()),
            details=f"Test detail {i}",
        ))
    await db_session.commit()

    login = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "saathi-admin-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login.json()["access_token"]

    # First page
    res = await async_client.get(
        "/api/v1/admin/audit-log?page=1&limit=3",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "entries" in data
    assert "total" in data
    assert data["total"] >= 5
    assert len(data["entries"]) == 3
    assert "action" in data["entries"][0]
    assert "timestamp" in data["entries"][0]
