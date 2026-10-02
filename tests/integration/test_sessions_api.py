import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_session_lifecycle(async_client: AsyncClient):
    # 1. Create a session
    payload = {"channel": "VOICE_CALL", "language": "hi"}
    res = await async_client.post("/api/v1/sessions", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert data["channel"] == "VOICE_CALL"
    assert data["status"] == "INITIALIZED"
    session_id = data["id"]

    # 2. Retrieve session
    res = await async_client.get(f"/api/v1/sessions/{session_id}")
    assert res.status_code == 200
    assert res.json()["id"] == session_id

    # 3. Close session
    res = await async_client.patch(f"/api/v1/sessions/{session_id}/close")
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"
    assert res.json()["closed_at"] is not None


@pytest.mark.integration
async def test_consent_flow(async_client: AsyncClient):
    # Create session
    session_res = await async_client.post("/api/v1/sessions", json={"channel": "WEB_AUDIO", "language": "en"})
    session_id = session_res.json()["id"]

    # Record Audio Recording consent
    consent_payload = {
        "session_id": session_id,
        "consent_type": "AUDIO_RECORDING",
        "status": "GRANTED",
        "notes": "Verbal assent obtained",
    }
    res = await async_client.post("/api/v1/consent", json=consent_payload)
    assert res.status_code == 201
    assert res.json()["consent_type"] == "AUDIO_RECORDING"

    # Record AI Assessment consent
    res = await async_client.post(
        "/api/v1/consent",
        json={"session_id": session_id, "consent_type": "AI_ASSESSMENT", "status": "GRANTED"},
    )
    assert res.status_code == 201

    # Fetch consents for session
    list_res = await async_client.get(f"/api/v1/consent/{session_id}")
    assert list_res.status_code == 200
    consents = list_res.json()
    assert len(consents) == 2

    # Reject nonexistent session
    fake_id = str(uuid.uuid4())
    bad_res = await async_client.post(
        "/api/v1/consent",
        json={"session_id": fake_id, "consent_type": "AI_ASSESSMENT", "status": "GRANTED"},
    )
    assert bad_res.status_code == 404


@pytest.mark.integration
async def test_case_triage_flow(async_client: AsyncClient):
    # Create session
    session_res = await async_client.post("/api/v1/sessions", json={"channel": "CHAT_TEXT", "language": "hi"})
    session_id = session_res.json()["id"]

    # Create Case
    case_payload = {
        "session_id": session_id,
        "priority": "HIGH",
        "initial_notes": "Immediate distress signals detected",
    }
    case_res = await async_client.post("/api/v1/cases", json=case_payload)
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]
    assert case_res.json()["priority"] == "HIGH"
    assert case_res.json()["status"] == "OPEN"

    # List cases in queue
    list_res = await async_client.get("/api/v1/cases?priority=HIGH")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Update case status
    update_res = await async_client.patch(
        f"/api/v1/cases/{case_id}/status?new_status=IN_REVIEW&assigned_to=responder_42"
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "IN_REVIEW"
    assert update_res.json()["assigned_to"] == "responder_42"
