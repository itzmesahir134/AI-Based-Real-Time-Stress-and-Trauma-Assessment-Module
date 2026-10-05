import pytest
import uuid
import base64
from httpx import AsyncClient

from packages.schemas import RiskBand
from services.api.db import (
    CaseModel,
    QualityResultModel,
    SessionModel,
    TranscriptModel,
    AuditLogModel,
)


@pytest.mark.asyncio
async def test_full_pipeline_persists_all_tables(async_client: AsyncClient, auth_client: AsyncClient, db_session):
    """Test that the orchestrator creates all expected DB records for a full session."""
    session_id = uuid.uuid4()
    
    # 1. Setup session
    db_session.add(SessionModel(id=session_id, channel="WEB_AUDIO"))
    await db_session.commit()
    
    # 2. Mock 1 second of silent/neutral audio to pass base64 check
    import numpy as np
    import soundfile as sf
    import io
    audio = np.zeros(16000, dtype=np.float32)
    buf = io.BytesIO()
    sf.write(buf, audio, 16000, format='WAV')
    audio_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    payload = {
        "session_id": str(session_id),
        "language": "hi",
        "audio_base64": audio_base64,
        "self_report": {
            "q1_distress": 2,
            "q2_safety": 1,
            "q3_urgency": 1,
            "q4_can_continue": 0,
            "support_needs": ["counselling"]
        },
        "context": {
            "incident_type": "stress",
            "ongoing_threat": False,
            "prior_case": False,
            "vulnerability_factors": [],
            "immediate_support_requested": False
        }
    }
    
    res = await async_client.post("/api/v1/assessment/run", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["session_id"] == str(session_id)
    assert "svi" in data
    assert data["assessment_status"] == "PARTIAL"  # Pure silence -> voice abstained -> PARTIAL
    assert data["case_id"] is not None
    
    # Check DB tables
    case = await db_session.get(CaseModel, uuid.UUID(data["case_id"]))
    assert case is not None
    assert case.session_id == session_id
    
    # Check Audit Log
    from sqlalchemy import select
    audit = (await db_session.execute(select(AuditLogModel).where(AuditLogModel.resource_id == str(case.id)))).scalar_one_or_none()
    assert audit is not None
    assert audit.action == "ASSESSMENT_COMPLETED"
    
    # Fetch reconstruction
    get_res = await auth_client.get(f"/api/v1/assessment/{session_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["case_id"] == str(case.id)


@pytest.mark.asyncio
async def test_crisis_override_sets_case_critical(async_client: AsyncClient, db_session):
    """Test scenario D equivalent: self report triggers crisis override -> CRITICAL band."""
    session_id = uuid.uuid4()
    db_session.add(SessionModel(id=session_id, channel="CHAT_TEXT"))
    await db_session.commit()
    
    payload = {
        "session_id": str(session_id),
        "language": "en",
        "self_report": {
            "q1_distress": 4,
            "q2_safety": 4, # Indicates immediate danger
            "q3_urgency": 4,
            "q4_can_continue": 0,
            "support_needs": []
        }
    }
    
    res = await async_client.post("/api/v1/assessment/run", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["safety_override"] is True
    assert data["risk_band"] == RiskBand.CRITICAL.value
    
    case_id = data["case_id"]
    case = await db_session.get(CaseModel, uuid.UUID(case_id))
    assert case.priority == RiskBand.CRITICAL.value


@pytest.mark.asyncio
async def test_missing_audio_abstains_voice_modality(async_client: AsyncClient, db_session):
    """Test that missing audio gracefully abstains from voice/text inference."""
    session_id = uuid.uuid4()
    db_session.add(SessionModel(id=session_id, channel="WEB_AUDIO"))
    await db_session.commit()
    
    payload = {
        "session_id": str(session_id),
        "language": "hi",
        "audio_base64": None, # Missing audio
        "self_report": {
            "q1_distress": 1,
            "q2_safety": 0,
            "q3_urgency": 0,
            "q4_can_continue": 0,
            "support_needs": []
        }
    }
    
    res = await async_client.post("/api/v1/assessment/run", json=payload)
    assert res.status_code == 201
    data = res.json()
    
    # SVI should still compute based on self report alone
    assert "svi" in data
    # Quality factors for voice/text should be 0 (abstained)
    assert data["quality"]["voice"] == 0.0 or data["quality"]["voice"] is None
    
