import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.integration
async def test_auth_login_success(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "saathi-admin-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "ADMIN"

@pytest.mark.asyncio
@pytest.mark.integration
async def test_auth_login_wrong_password(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
@pytest.mark.integration
async def test_rbac_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/v1/cases")
    assert response.status_code == 401
    
@pytest.mark.asyncio
@pytest.mark.integration
async def test_rbac_authorized(async_client: AsyncClient):
    # Login as responder
    login_resp = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "responder", "password": "saathi-resp-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_resp.json()["access_token"]
    
    # Access cases
    response = await async_client.get(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.integration
async def test_rbac_forbidden(async_client: AsyncClient):
    # Login as auditor
    login_resp = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "auditor", "password": "saathi-audit-2026"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_resp.json()["access_token"]
    
    # Access cases (auditor doesn't have cases:write, but wait, auditor has cases:read.
    # The endpoint cases GET require_role("RESPONDER", "SUPERVISOR", "ADMIN"). 
    # Auditor is not in that list, so it should be forbidden.
    response = await async_client.get(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
