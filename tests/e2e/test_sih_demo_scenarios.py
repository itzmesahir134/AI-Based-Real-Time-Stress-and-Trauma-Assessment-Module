"""E2E Test Suite for the 5 SIH 2026 Canonical Triage Scenarios (PS 26093).
Validates multi-modal ingestion, acoustic quality gating, self-report scoring,
safety override escalation, and DB persistence.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.db import SessionModel, CaseModel
from tools.demo_scenario_runner import SCENARIOS, load_audio_base64


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
async def test_sih_demo_scenario_e2e(
    scenario: dict,
    auth_client: AsyncClient,
    db_session: AsyncSession,
):
    """Executes a canonical SIH scenario against the in-process test application."""
    session_id = uuid.uuid4()

    # 1. Create Session
    session_res = await auth_client.post(
        "/api/v1/sessions",
        json={"channel": "WEB_AUDIO", "language": scenario["language"]},
    )
    assert session_res.status_code in (200, 201)
    session_id_str = session_res.json()["id"]

    # 2. Record Consents
    await auth_client.post(
        "/api/v1/consent",
        json={
            "session_id": session_id_str,
            "consent_type": "AUDIO_RECORDING",
            "status": "GRANTED",
        },
    )
    await auth_client.post(
        "/api/v1/consent",
        json={
            "session_id": session_id_str,
            "consent_type": "AI_ASSESSMENT",
            "status": "GRANTED",
        },
    )

    # 3. Load Audio if required
    audio_base64 = None
    if scenario["audio_file"]:
        audio_base64 = load_audio_base64(scenario["audio_file"])

    # 4. Execute Assessment
    assessment_payload = {
        "session_id": session_id_str,
        "language": scenario["language"],
        "audio_base64": audio_base64,
        "self_report": scenario["self_report"],
        "context": scenario["context"],
    }

    res = await auth_client.post("/api/v1/assessment/run", json=assessment_payload)
    assert res.status_code in (200, 201), res.text
    result = res.json()

    expected = scenario["expected"]

    # Assertions
    assert (
        result["risk_band"] in expected["acceptable_bands"]
    ), f"Scenario {scenario['id']}: expected band in {expected['acceptable_bands']}, got {result['risk_band']}"

    assert (
        result["safety_override"] == expected["expected_safety_override"]
    ), f"Scenario {scenario['id']}: expected safety override {expected['expected_safety_override']}, got {result['safety_override']}"

    if "acceptable_statuses" in expected:
        assert result["assessment_status"] in expected["acceptable_statuses"]

    if "min_evidence_coverage" in expected:
        assert result["evidence_coverage"] >= expected["min_evidence_coverage"]

    # Verify Case record creation in DB
    case_id = result.get("case_id")
    assert case_id is not None
    case_res = await auth_client.get(f"/api/v1/cases/{case_id}")
    assert case_res.status_code == 200
    case_data = case_res.json()
    assert case_data["priority"] == result["risk_band"]
