import pytest
from httpx import AsyncClient
from tests.integration.test_audio_api import create_test_wav_bytes


@pytest.mark.integration
async def test_audio_features_endpoint(async_client: AsyncClient):
    wav_bytes = create_test_wav_bytes(duration=1.0)
    files = {"file": ("test.wav", wav_bytes, "audio/wav")}

    res = await async_client.post("/api/v1/audio/features", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "pitch_mean" in data
    assert "mfcc_mean" in data
    assert len(data["mfcc_mean"]) == 13
    assert "voiced_fraction" in data


@pytest.mark.integration
async def test_voice_inference_endpoint(async_client: AsyncClient):
    payload = {
        "features": {
            "pitch_mean": 210.0,
            "pitch_std": 35.0,
            "pitch_range": 90.0,
            "speech_rate_syl_per_sec": 4.5,
            "pause_ratio": 0.25,
            "pause_count": 2,
            "energy_mean": 0.12,
            "energy_std": 0.05,
            "jitter": 0.02,
            "shimmer": 0.04,
            "mfcc_mean": [0.0] * 13,
            "mfcc_std": [0.0] * 13,
            "spectral_centroid_mean": 1500.0,
            "zcr_mean": 0.08,
            "voiced_fraction": 0.8,
            "feature_schema_version": "v1.0.0",
        },
        "quality": {
            "quality_score": 0.90,
            "distortion_flags": [],
        },
        "language": "en",
    }
    res = await async_client.post("/api/v1/inference/voice", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "score" in data
    assert data["score"] is not None
    assert "confidence" in data
    assert "evidence_features" in data


@pytest.mark.integration
async def test_text_inference_endpoint(async_client: AsyncClient):
    payload = {
        "text": "Please help me! He has a knife and threatens to hurt me right now!",
        "language": "en",
    }
    res = await async_client.post("/api/v1/inference/text", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["score"] is not None
    assert data["score"] > 50.0
    assert any("threat" in ind for ind in data["indicators"])


@pytest.mark.integration
async def test_crisis_inference_endpoint(async_client: AsyncClient):
    payload = {
        "text": "I can't go on anymore, I want to kill myself.",
    }
    res = await async_client.post("/api/v1/inference/crisis", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["safety_flag"] is True
    assert data["crisis_type"] == "suicidal_ideation"


@pytest.mark.integration
async def test_self_report_endpoint(async_client: AsyncClient):
    payload = {
        "q1_distress": 3,
        "q2_safety": 2,
        "q3_urgency": 3,
        "q4_can_continue": 1,
        "support_needs": ["counselling", "medical"],
    }
    res = await async_client.post("/api/v1/self-report", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "score" in data
    assert data["score"] > 0.0
    assert data["completeness"] == 1.0


@pytest.mark.integration
async def test_context_endpoint(async_client: AsyncClient):
    payload = {
        "incident_type": "domestic_violence",
        "ongoing_threat": True,
        "prior_case": True,
        "vulnerability_factors": ["minor"],
        "immediate_support_requested": True,
    }
    res = await async_client.post("/api/v1/context", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["score"] >= 80.0
    assert "active_ongoing_threat" in data["risk_factors"]


@pytest.mark.integration
async def test_svi_calculate_endpoint(async_client: AsyncClient):
    payload = {
        "modality_scores": {
            "voice": 72.0,
            "text": 65.0,
            "self_report": 80.0,
            "context": 60.0,
        },
        "quality": {
            "voice": 0.85,
            "text": 0.90,
            "self_report": 1.0,
            "context": 1.0,
        },
        "force_safety_flag": False,
        "support_needs": ["counselling", "legal"],
    }
    res = await async_client.post("/api/v1/svi/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "svi" in data
    assert 65.0 <= data["svi"] <= 78.0
    assert data["risk_band"] in ["HIGH", "CRITICAL"]
    assert len(data["support_recommendations"]) > 0


@pytest.mark.integration
async def test_recommendations_endpoint(async_client: AsyncClient):
    payload = {
        "priority": "CRITICAL",
        "support_needs": ["police", "medical"],
        "safety_override": True,
    }
    res = await async_client.post("/api/v1/support/recommend", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["priority"] == "CRITICAL"
    assert any("IMMEDIATE_ESCALATION" in r for r in data["recommendations"])
    assert any("POLICE_LIAISON" in r for r in data["recommendations"])
