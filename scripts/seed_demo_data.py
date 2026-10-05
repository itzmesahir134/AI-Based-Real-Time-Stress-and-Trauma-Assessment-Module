"""Seed realistic demo datasets into SaathiAI database for SIH 2026 hackathon demo."""

import argparse
import asyncio
from datetime import datetime, timezone, timedelta
import json
import os
import random
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from services.api.db.models import (
    AuditLogModel,
    Base,
    CaseModel,
    ContextResultModel,
    CrisisResultModel,
    QualityResultModel,
    RecommendationModel,
    SelfReportModel,
    SessionModel,
    SVIResultModel,
    TextInferenceModel,
    TranscriptModel,
    VoiceFeatureModel,
    VoiceInferenceModel,
)


SAMPLE_SCENARIOS = [
    # --- CRITICAL (Safety Overrides & Active Threats) ---
    {
        "risk_band": "CRITICAL",
        "svi": 96.5,
        "confidence": 0.96,
        "safety_flag": True,
        "crisis_type": "immediate_threat",
        "language": "hi",
        "transcript": "बचाओ! वह चाकू लेकर अंदर घुस आया है और दरवाजा तोड़ रहा है! प्लीज पुलिस भेजो तुरंत!",
        "recommendations": ["IMMEDIATE_POLICE_DISPATCH", "CRISIS_TEAM_ALERT", "LOCATION_TRACING"],
        "reasoning": "Active home intrusion with weapon threat. Critical life safety flag triggered.",
        "incident_type": "domestic_violence_weapon",
        "ongoing_threat": True,
        "vulnerability_factors": ["minor_present", "isolated_location"],
    },
    {
        "risk_band": "CRITICAL",
        "svi": 94.0,
        "confidence": 0.94,
        "safety_flag": True,
        "crisis_type": "suicide_risk",
        "language": "en",
        "transcript": "I have taken all the sleeping pills and I can't breathe. Nobody cares about me anymore.",
        "recommendations": ["EMERGENCY_AMBULANCE_DISPATCH", "PSYCHIATRIC_INTERVENTION", "CALLER_LINE_LOCK"],
        "reasoning": "Explicit lethal overdose ingestion. Critical emergency medical response required.",
        "incident_type": "self_harm_overdose",
        "ongoing_threat": True,
        "vulnerability_factors": ["unaccompanied_caller"],
    },
    {
        "risk_band": "CRITICAL",
        "svi": 88.0,
        "confidence": 0.91,
        "safety_flag": True,
        "crisis_type": "immediate_violence",
        "language": "hi-Latn",
        "transcript": "Bachao mujhe! Bahar se aag laga di hai room ke, dhuan bhar raha hai!",
        "recommendations": ["FIRE_AND_RESCUE_DISPATCH", "POLICE_EVACUATION", "EMERGENCY_TRIAGE"],
        "reasoning": "Active arson / smoke entrapment emergency with severe respiratory danger.",
        "incident_type": "arson_threat",
        "ongoing_threat": True,
        "vulnerability_factors": ["trapped_room", "elderly_dependent"],
    },
    {
        "risk_band": "CRITICAL",
        "svi": 89.5,
        "confidence": 0.93,
        "safety_flag": True,
        "crisis_type": "immediate_threat",
        "language": "en",
        "transcript": "My stalker is standing outside my window right now with an iron rod. He is yelling he will kill me.",
        "recommendations": ["IMMEDIATE_PATROL_DISPATCH", "SAFETY_INSTRUCTIONS", "CALL_RECORDING_FLAGGED"],
        "reasoning": "Active stalking with verbal threat to life and visible weapon outside residence.",
        "incident_type": "stalking_threat",
        "ongoing_threat": True,
        "vulnerability_factors": ["living_alone"],
    },
    {
        "risk_band": "CRITICAL",
        "svi": 91.0,
        "confidence": 0.92,
        "safety_flag": True,
        "crisis_type": "immediate_violence",
        "language": "hi",
        "transcript": "मुझ पर हमला हुआ है, बहुत खून बह रहा है और सिर में चक्कर आ रहे हैं।",
        "recommendations": ["EMERGENCY_AMBULANCE_DISPATCH", "FIRST_AID_GUIDANCE", "POLICE_ALERT"],
        "reasoning": "Physical assault resulting in severe bleeding and head trauma.",
        "incident_type": "physical_assault",
        "ongoing_threat": False,
        "vulnerability_factors": ["severe_injury"],
    },

    # --- HIGH RISK ---
    {
        "risk_band": "HIGH",
        "svi": 72.0,
        "confidence": 0.88,
        "safety_flag": False,
        "crisis_type": None,
        "language": "hi",
        "transcript": "मेरे पति रोज़ मुझे पीटते हैं और बच्चों को भूखा रखते हैं। मुझे शेल्टर होम चाहिए।",
        "recommendations": ["WOMEN_SHELTER_COORDINATION", "LEGAL_COUNSELING", "PROTECTION_OFFICER_REFERRAL"],
        "reasoning": "Chronic domestic violence with child endangerment; caller urgently seeking shelter.",
        "incident_type": "domestic_abuse",
        "ongoing_threat": True,
        "vulnerability_factors": ["children_at_risk", "financial_dependence"],
    },
    {
        "risk_band": "HIGH",
        "svi": 68.5,
        "confidence": 0.85,
        "safety_flag": False,
        "crisis_type": None,
        "language": "en",
        "transcript": "I'm having a massive panic attack. My heart is beating at 160 bpm and I feel like I'm losing my mind.",
        "recommendations": ["PSYCHOLOGICAL_FIRST_AID", "TELE_COUNSELING", "ANXIETY_DE_ESCALATION"],
        "reasoning": "Severe acute panic attack with tachycardia and dissociative symptoms.",
        "incident_type": "panic_disorder",
        "ongoing_threat": False,
        "vulnerability_factors": ["prior_anxiety_history"],
    },
    {
        "risk_band": "HIGH",
        "svi": 66.0,
        "confidence": 0.82,
        "safety_flag": False,
        "crisis_type": None,
        "language": "hi-Latn",
        "transcript": "College me senior ladke roz hostel ke bahar gher kar threaten karte hain. Bohot dar lagta hai.",
        "recommendations": ["CAMPUS_SAFETY_ESCALATION", "ANTIRAGGING_CELL_NOTICE", "PSYCHOLOGICAL_COUNSELING"],
        "reasoning": "Persistent targeted harassment and bullying outside hostel perimeter.",
        "incident_type": "ragging_harassment",
        "ongoing_threat": True,
        "vulnerability_factors": ["student_hosteller"],
    },
    {
        "risk_band": "HIGH",
        "svi": 74.0,
        "confidence": 0.87,
        "safety_flag": False,
        "crisis_type": None,
        "language": "en",
        "transcript": "My employer locked my passport and has confined me to the basement for three days without food.",
        "recommendations": ["LABOR_ENFORCEMENT_TASKFORCE", "RESCUE_OPERATION", "CONSULAR_LEGAL_AID"],
        "reasoning": "Human trafficking / forced labor indicators with physical unlawful confinement.",
        "incident_type": "unlawful_confinement",
        "ongoing_threat": True,
        "vulnerability_factors": ["migrant_worker", "withheld_documents"],
    },
    {
        "risk_band": "HIGH",
        "svi": 64.5,
        "confidence": 0.84,
        "safety_flag": False,
        "crisis_type": None,
        "language": "hi",
        "transcript": "मुझे बहुत दिनों से डिप्रेशन है और जीने की इच्छा खत्म हो गई है, पर मैं किसी को बता नहीं पा रही।",
        "recommendations": ["MENTAL_HEALTH_HELPLINE_REFERRAL", "ONGOING_TELE_SUPPORT", "WELLNESS_FOLLOW_UP"],
        "reasoning": "Severe chronic depression with passive death wishes. Immediate empathetic support indicated.",
        "incident_type": "clinical_depression",
        "ongoing_threat": False,
        "vulnerability_factors": ["social_isolation"],
    },

    # --- MODERATE RISK ---
    {
        "risk_band": "MODERATE",
        "svi": 42.0,
        "confidence": 0.80,
        "safety_flag": False,
        "crisis_type": None,
        "language": "en",
        "transcript": "I am feeling extremely stressed because of my final semester engineering exams and career pressure.",
        "recommendations": ["STUDENT_COUNSELING", "STRESS_MANAGEMENT_WORKSHOP", "PEER_SUPPORT_GROUP"],
        "reasoning": "Academic distress and anticipatory anxiety. No immediate harm factors present.",
        "incident_type": "academic_stress",
        "ongoing_threat": False,
        "vulnerability_factors": [],
    },
    {
        "risk_band": "MODERATE",
        "svi": 38.0,
        "confidence": 0.78,
        "safety_flag": False,
        "crisis_type": None,
        "language": "hi",
        "transcript": "घर में ज़मीनी विवाद को लेकर बहुत बहस हुई है। मानसिक रूप से काफी तनाव महसूस हो रहा है।",
        "recommendations": ["FAMILY_MEDIATION", "LEGAL_ADVICE_REFERRAL", "STRESS_COPING_RESOURCES"],
        "reasoning": "Property dispute causing situational familial tension. Legal mediation advised.",
        "incident_type": "property_dispute",
        "ongoing_threat": False,
        "vulnerability_factors": [],
    },
    {
        "risk_band": "MODERATE",
        "svi": 46.0,
        "confidence": 0.82,
        "safety_flag": False,
        "crisis_type": None,
        "language": "hi-Latn",
        "transcript": "Office me boss continuously overload de raha hai aur publicly insult karta hai. Sleep cycle spoil ho gayi hai.",
        "recommendations": ["WORKPLACE_STRESS_COUNSELING", "HR_ADVOCACY_GUIDELINES", "SLEEP_HYGIENE_PLAN"],
        "reasoning": "Workplace emotional harassment leading to burnout and insomnia.",
        "incident_type": "workplace_stress",
        "ongoing_threat": True,
        "vulnerability_factors": [],
    },
    {
        "risk_band": "MODERATE",
        "svi": 34.0,
        "confidence": 0.79,
        "safety_flag": False,
        "crisis_type": None,
        "language": "en",
        "transcript": "Going through a rough divorce proceeding. Just needed someone neutral to talk through the custody details.",
        "recommendations": ["FAMILY_LEGAL_COUNSEL", "RELATIONSHIP_SUPPORT", "PARENTING_MEDIATION"],
        "reasoning": "Marital separation distress. Constructive legal and emotional counseling provided.",
        "incident_type": "divorce_custody",
        "ongoing_threat": False,
        "vulnerability_factors": [],
    },

    # --- LOW RISK ---
    {
        "risk_band": "LOW",
        "svi": 14.0,
        "confidence": 0.89,
        "safety_flag": False,
        "crisis_type": None,
        "language": "en",
        "transcript": "Good morning, could you please provide the contact numbers for the nearest government women empowerment center?",
        "recommendations": ["RESOURCE_DIRECTORY_LOOKUP", "SMS_INFORMATION_DISPATCH"],
        "reasoning": "Informational inquiry regarding government welfare resources. Zero distress markers.",
        "incident_type": "general_inquiry",
        "ongoing_threat": False,
        "vulnerability_factors": [],
    },
    {
        "risk_band": "LOW",
        "svi": 12.0,
        "confidence": 0.91,
        "safety_flag": False,
        "crisis_type": None,
        "language": "hi",
        "transcript": "नमस्ते, क्या आपके पास बाल अधिकार आयोग के टोल-फ्री नंबर की जानकारी है?",
        "recommendations": ["DIRECT_DIRECTORY_ROUTING", "INFORMATION_BROCHURE_SMS"],
        "reasoning": "Routine administrative assistance for child rights directory.",
        "incident_type": "directory_request",
        "ongoing_threat": False,
        "vulnerability_factors": [],
    },
    {
        "risk_band": "LOW",
        "svi": 18.0,
        "confidence": 0.85,
        "safety_flag": False,
        "crisis_type": None,
        "language": "hi-Latn",
        "transcript": "Maine pichle hafte counseling attend ki thi, just wanted to confirm my next appointment slot.",
        "recommendations": ["APPOINTMENT_SCHEDULING", "CALENDAR_SYNC_CONFIRMATION"],
        "reasoning": "Follow-up schedule inquiry from existing beneficiary. Positive progress noted.",
        "incident_type": "appointment_followup",
        "ongoing_threat": False,
        "vulnerability_factors": [],
    },
]


async def seed_data(db_url: str):
    """Seed comprehensive demo database."""
    print(f"--- Seeding SaathiAI Demo Database ({db_url}) ---")
    is_sqlite = db_url.startswith("sqlite")
    engine_kwargs = {} if is_sqlite else {"pool_pre_ping": True}
    
    engine = create_async_engine(db_url, **engine_kwargs)
    SessionMaker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionMaker() as db:
        now = datetime.now(timezone.utc)
        for idx, scenario in enumerate(SAMPLE_SCENARIOS):
            sess_id = uuid.uuid4()
            case_id = uuid.uuid4()
            svi_id = uuid.uuid4()
            quality_id = uuid.uuid4()
            created_time = now - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))

            # Session
            session_obj = SessionModel(
                id=sess_id,
                channel=random.choice(["phone_call", "web_rtc", "whatsapp_audio"]),
                status="COMPLETED",
                language=scenario["language"],
                created_at=created_time,
            )
            db.add(session_obj)

            # Case
            case_obj = CaseModel(
                id=case_id,
                session_id=sess_id,
                status="IN_REVIEW" if scenario["risk_band"] in ["CRITICAL", "HIGH"] else "RESOLVED",
                priority=scenario["risk_band"],
                created_at=created_time,
            )
            db.add(case_obj)

            # Quality
            db.add(QualityResultModel(
                id=quality_id,
                session_id=sess_id,
                quality_score=0.88,
                snr_estimate=24.5,
                clipping_ratio=0.002,
                speech_ratio=0.85,
                distortion_flags=[],
            ))

            # Transcript
            db.add(TranscriptModel(
                session_id=sess_id,
                quality_id=quality_id,
                language=scenario["language"],
                full_text=scenario["transcript"],
                duration_seconds=18.5,
            ))

            # Voice Feature
            voice_dict = {
                "pitch_mean": 230.0 if scenario["risk_band"] in ["CRITICAL", "HIGH"] else 150.0,
                "pitch_std": 65.0 if scenario["risk_band"] in ["CRITICAL", "HIGH"] else 15.0,
                "pitch_range": 190.0 if scenario["risk_band"] in ["CRITICAL", "HIGH"] else 50.0,
                "jitter": 0.045 if scenario["risk_band"] in ["CRITICAL", "HIGH"] else 0.010,
                "shimmer": 0.075 if scenario["risk_band"] in ["CRITICAL", "HIGH"] else 0.020,
                "energy_mean": 0.08,
                "energy_std": 0.06,
                "pause_ratio": 0.45 if scenario["risk_band"] in ["CRITICAL", "HIGH"] else 0.15,
                "speech_rate_syl_per_sec": 6.2 if scenario["risk_band"] in ["CRITICAL", "HIGH"] else 4.0,
                "voiced_fraction": 0.85,
            }
            db.add(VoiceFeatureModel(
                session_id=sess_id,
                features=voice_dict,
                schema_version="v1.0.0",
            ))

            # Voice Inference
            db.add(VoiceInferenceModel(
                session_id=sess_id,
                score=min(scenario["svi"] + random.uniform(-4, 4), 100.0),
                confidence=scenario["confidence"],
                model_version="v1.1.0-gb-ensemble",
                evidence_features=["pitch_variability", "vocal_tremor"] if scenario["risk_band"] in ["CRITICAL", "HIGH"] else ["calm_prosody"],
            ))

            # Text Inference
            db.add(TextInferenceModel(
                session_id=sess_id,
                score=min(scenario["svi"] + random.uniform(-3, 3), 100.0),
                confidence=scenario["confidence"],
                model_version="v1.1.0-tfidf-rf",
                indicators=[f"incident: {scenario['incident_type']}"],
            ))

            # Self Report
            db.add(SelfReportModel(
                session_id=sess_id,
                q1_distress=4 if scenario["risk_band"] == "CRITICAL" else (3 if scenario["risk_band"] == "HIGH" else 1),
                q2_safety=4 if scenario["safety_flag"] else 1,
                q3_urgency=4 if scenario["risk_band"] == "CRITICAL" else 2,
                q4_can_continue=0 if scenario["risk_band"] == "CRITICAL" else 4,
                support_needs=scenario["recommendations"],
                score=90.0 if scenario["risk_band"] == "CRITICAL" else 40.0,
                safety_flag=scenario["safety_flag"],
                completeness=1.0,
            ))

            # Context
            db.add(ContextResultModel(
                session_id=sess_id,
                incident_type=scenario["incident_type"],
                ongoing_threat=scenario["ongoing_threat"],
                prior_case=False,
                vulnerability_factors=scenario["vulnerability_factors"],
                immediate_support_requested=scenario["safety_flag"],
                score=85.0 if scenario["ongoing_threat"] else 20.0,
                completeness=1.0,
            ))

            # Crisis Result
            db.add(CrisisResultModel(
                session_id=sess_id,
                safety_flag=scenario["safety_flag"],
                crisis_type=scenario["crisis_type"],
                confidence=1.0 if scenario["safety_flag"] else 0.0,
                evidence=[scenario["reasoning"]] if scenario["safety_flag"] else [],
                rule_triggered=scenario["safety_flag"],
                model_triggered=scenario["safety_flag"],
            ))

            # SVI Result
            db.add(SVIResultModel(
                id=svi_id,
                session_id=sess_id,
                svi=scenario["svi"],
                risk_band=scenario["risk_band"],
                confidence=scenario["confidence"],
                evidence_coverage=0.92,
                assessment_status="COMPLETE",
                safety_override=scenario["safety_flag"],
                model_config_version="svi-v1.0",
            ))

            # Recommendations
            db.add(RecommendationModel(
                session_id=sess_id,
                svi_result_id=svi_id,
                priority=scenario["risk_band"],
                recommendations=scenario["recommendations"],
                explanation={
                    "summary": scenario["reasoning"],
                    "contributors": [scenario["incident_type"]],
                    "confidence": scenario["confidence"]
                },
            ))

            # Audit Log
            db.add(AuditLogModel(
                user_id="system_seeder",
                action="ASSESSMENT_PIPELINE_EXECUTED",
                resource_type="case",
                resource_id=str(case_id),
                details=json.dumps({
                    "risk_band": scenario["risk_band"],
                    "svi": scenario["svi"],
                    "safety_override": scenario["safety_flag"]
                }),
                timestamp=created_time,
            ))

        await db.commit()
        print(f"[SUCCESS] Successfully seeded {len(SAMPLE_SCENARIOS)} realistic triage cases and audit logs into database.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed SaathiAI demo data")
    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL")
    args = parser.parse_args()

    # Determine database URL: argument -> env var -> sqlite fallback
    target_url = args.db_url or os.getenv("DATABASE_URL")
    if not target_url or "saathi_password" in target_url:
        # Default to local sqlite for quick standalone demo
        target_url = "sqlite+aiosqlite:///saathi_demo.db"

    try:
        asyncio.run(seed_data(target_url))
    except Exception as e:
        print(f"[WARNING] Seeding to {target_url} failed: {e}. Falling back to SQLite...")
        fallback_url = "sqlite+aiosqlite:///saathi_demo.db"
        asyncio.run(seed_data(fallback_url))
