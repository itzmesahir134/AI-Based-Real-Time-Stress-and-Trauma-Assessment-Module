import pytest
from uuid import uuid4
from pydantic import ValidationError

from packages.schemas import (
    AssessmentStatus,
    CaseCreate,
    CaseResponse,
    CaseStatus,
    ChannelEnum,
    ConsentCreate,
    ConsentResponse,
    ConsentStatus,
    ConsentType,
    MasterAssessmentObject,
    ModalityContributions,
    ModalityScores,
    QualityFactors,
    RiskBand,
    SessionCreate,
    SessionResponse,
    SessionStatusEnum,
    SVIResult,
)


@pytest.mark.unit
def test_session_schemas():
    # Valid session creation
    session_in = SessionCreate(channel=ChannelEnum.VOICE_CALL, language="hi")
    assert session_in.channel == ChannelEnum.VOICE_CALL
    assert session_in.language == "hi"

    # Valid session response
    session_out = SessionResponse(
        id=uuid4(),
        channel=session_in.channel,
        status=SessionStatusEnum.ACTIVE,
        language="hi",
    )
    assert session_out.status == SessionStatusEnum.ACTIVE

    # Invalid channel raises ValidationError
    with pytest.raises(ValidationError):
        SessionCreate(channel="TELEGRAM")  # type: ignore[arg-type]


@pytest.mark.unit
def test_consent_schemas():
    session_id = uuid4()
    consent_in = ConsentCreate(
        session_id=session_id,
        consent_type=ConsentType.AUDIO_RECORDING,
        status=ConsentStatus.GRANTED,
        notes="Caller consented verbally",
    )
    assert consent_in.status == ConsentStatus.GRANTED

    consent_out = ConsentResponse(
        id=uuid4(),
        session_id=session_id,
        consent_type=ConsentType.AUDIO_RECORDING,
        status=ConsentStatus.GRANTED,
    )
    assert consent_out.session_id == session_id


@pytest.mark.unit
def test_case_schemas():
    session_id = uuid4()
    case_in = CaseCreate(session_id=session_id, priority=RiskBand.HIGH)
    assert case_in.priority == RiskBand.HIGH

    case_out = CaseResponse(
        id=uuid4(),
        session_id=session_id,
        status=CaseStatus.OPEN,
        priority=RiskBand.HIGH,
    )
    assert case_out.status == CaseStatus.OPEN


@pytest.mark.unit
def test_master_assessment_object():
    session_id = uuid4()
    assessment = MasterAssessmentObject(
        session_id=session_id,
        assessment_status=AssessmentStatus.COMPLETE,
        svi=72.5,
        risk_band=RiskBand.HIGH,
        confidence=0.88,
        evidence_coverage=0.92,
        safety_override=False,
        modality_scores=ModalityScores(voice=70.0, text=75.0, self_report=80.0),
        quality=QualityFactors(voice=0.85, text=0.95),
        contributions=ModalityContributions(voice=25.0, text=30.0, self_report=17.5),
        contributors=["high vocal jitter", "acute distress phrasing"],
        support_recommendations=["Immediate responder contact"],
    )
    assert assessment.svi == 72.5
    assert assessment.risk_band == RiskBand.HIGH
    assert assessment.modality_scores.voice == 70.0


@pytest.mark.unit
def test_svi_range_bounds():
    session_id = uuid4()

    # SVI > 100 must fail
    with pytest.raises(ValidationError):
        SVIResult(
            session_id=session_id,
            svi=105.0,
            risk_band=RiskBand.CRITICAL,
            confidence=0.9,
            evidence_coverage=1.0,
        )

    # SVI < 0 must fail
    with pytest.raises(ValidationError):
        SVIResult(
            session_id=session_id,
            svi=-1.0,
            risk_band=RiskBand.LOW,
            confidence=0.9,
            evidence_coverage=1.0,
        )

    # Confidence > 1.0 must fail
    with pytest.raises(ValidationError):
        SVIResult(
            session_id=session_id,
            svi=50.0,
            risk_band=RiskBand.MODERATE,
            confidence=1.5,
            evidence_coverage=1.0,
        )
