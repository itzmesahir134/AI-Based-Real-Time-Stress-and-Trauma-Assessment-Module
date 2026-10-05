import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import CHAR, TypeDecorator

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.
    Uses PostgreSQL's native UUID type, or CHAR(36) on SQLite.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value


class JSONEncodedType(TypeDecorator):
    """Platform-independent JSON type.
    Uses PostgreSQL's native JSONB type, or standard JSON on SQLite.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class SessionModel(Base):
    """Spec §23: sessions table."""
    __tablename__ = "sessions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    channel = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="INITIALIZED")
    language = Column(String(32), nullable=True, default="hi")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    closed_at = Column(DateTime(timezone=True), nullable=True)

    consents = relationship("ConsentModel", back_populates="session", cascade="all, delete-orphan")
    cases = relationship("CaseModel", back_populates="session", cascade="all, delete-orphan")
    svi_results = relationship("SVIResultModel", back_populates="session", cascade="all, delete-orphan")
    audio_assets = relationship("AudioAssetModel", back_populates="session", cascade="all, delete-orphan")
    quality_results = relationship("QualityResultModel", back_populates="session", cascade="all, delete-orphan")
    transcripts = relationship("TranscriptModel", back_populates="session", cascade="all, delete-orphan")
    voice_features = relationship("VoiceFeatureModel", back_populates="session", cascade="all, delete-orphan")
    voice_inferences = relationship("VoiceInferenceModel", back_populates="session", cascade="all, delete-orphan")
    text_inferences = relationship("TextInferenceModel", back_populates="session", cascade="all, delete-orphan")
    self_reports = relationship("SelfReportModel", back_populates="session", cascade="all, delete-orphan")
    context_results = relationship("ContextResultModel", back_populates="session", cascade="all, delete-orphan")
    crisis_results = relationship("CrisisResultModel", back_populates="session", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationModel", back_populates="session", cascade="all, delete-orphan")


class ConsentModel(Base):
    """Spec §22: consents table."""
    __tablename__ = "consents"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    consent_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    notes = Column(Text, nullable=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="consents")


class CaseModel(Base):
    """Spec §22: cases table."""
    __tablename__ = "cases"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(32), nullable=False, default="OPEN")
    priority = Column(String(16), nullable=False, default="LOW")
    assigned_to = Column(String(64), nullable=True)
    initial_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="cases")
    human_reviews = relationship("HumanReviewModel", back_populates="case", cascade="all, delete-orphan")
    audio_assets = relationship("AudioAssetModel", back_populates="case", cascade="all, delete-orphan")


class SVIResultModel(Base):
    """Spec §23: svi_results table."""
    __tablename__ = "svi_results"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    svi = Column(Numeric(5, 2), nullable=False)
    risk_band = Column(String(16), nullable=False)
    confidence = Column(Numeric(4, 3), nullable=False)
    evidence_coverage = Column(Numeric(4, 3), nullable=False)
    assessment_status = Column(String(32), nullable=False, default="COMPLETE")
    safety_override = Column(Boolean, nullable=False, default=False)
    model_config_version = Column(String(64), nullable=False, default="v1.0.0")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="svi_results")
    recommendations = relationship("RecommendationModel", back_populates="svi_result")


class AuditLogModel(Base):
    """Spec §22, §39: audit_logs table."""
    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AudioAssetModel(Base):
    """Spec M01 / M02: audio_assets table."""
    __tablename__ = "audio_assets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True)
    case_id = Column(GUID, ForeignKey("cases.id", ondelete="CASCADE"), nullable=True)
    s3_key = Column(String(512), nullable=False)
    duration_seconds = Column(Numeric(7, 2), nullable=True)
    format = Column(String(32), nullable=False, default="wav")
    sample_rate = Column(Integer, nullable=False, default=16000)
    channels = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="audio_assets")
    case = relationship("CaseModel", back_populates="audio_assets")


class QualityResultModel(Base):
    """Spec M04: quality_results table."""
    __tablename__ = "quality_results"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    quality_score = Column(Numeric(4, 3), nullable=False)
    snr_estimate = Column(Numeric(5, 2), nullable=True)
    clipping_ratio = Column(Numeric(4, 3), nullable=False, default=0.0)
    speech_ratio = Column(Numeric(4, 3), nullable=False, default=1.0)
    packet_loss = Column(Numeric(4, 3), nullable=True)
    distortion_flags = Column(JSONEncodedType, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="quality_results")
    transcripts = relationship("TranscriptModel", back_populates="quality")


class TranscriptModel(Base):
    """Spec M07: transcripts table."""
    __tablename__ = "transcripts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    quality_id = Column(GUID, ForeignKey("quality_results.id", ondelete="SET NULL"), nullable=True)
    language = Column(String(16), nullable=False, default="hi")
    full_text = Column(Text, nullable=False, default="")
    duration_seconds = Column(Numeric(7, 2), nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="transcripts")
    quality = relationship("QualityResultModel", back_populates="transcripts")
    segments = relationship("TranscriptSegmentModel", back_populates="transcript", cascade="all, delete-orphan")


class TranscriptSegmentModel(Base):
    """Spec M07: transcript_segments table."""
    __tablename__ = "transcript_segments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    transcript_id = Column(GUID, ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    segment_order = Column(Integer, nullable=False, default=0)
    text = Column(Text, nullable=False)
    start_time = Column(Numeric(7, 2), nullable=False, default=0.0)
    end_time = Column(Numeric(7, 2), nullable=False, default=0.0)
    confidence = Column(Numeric(4, 3), nullable=False, default=1.0)
    language = Column(String(16), nullable=False, default="hi")

    transcript = relationship("TranscriptModel", back_populates="segments")


class VoiceFeatureModel(Base):
    """Spec M08: voice_features table."""
    __tablename__ = "voice_features"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    features = Column(JSONEncodedType, nullable=False)
    schema_version = Column(String(32), nullable=False, default="v1.0.0")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="voice_features")


class VoiceInferenceModel(Base):
    """Spec M09: voice_inferences table."""
    __tablename__ = "voice_inferences"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    score = Column(Numeric(5, 2), nullable=True)
    confidence = Column(Numeric(4, 3), nullable=False, default=0.0)
    evidence_features = Column(JSONEncodedType, nullable=False, default=list)
    model_version = Column(String(64), nullable=False, default="v1.0.0-heuristic")
    abstained = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="voice_inferences")


class TextInferenceModel(Base):
    """Spec M12: text_inferences table."""
    __tablename__ = "text_inferences"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    score = Column(Numeric(5, 2), nullable=True)
    confidence = Column(Numeric(4, 3), nullable=False, default=0.0)
    indicators = Column(JSONEncodedType, nullable=False, default=list)
    model_version = Column(String(64), nullable=False, default="v1.0.0-lexicon-heuristic")
    language = Column(String(16), nullable=False, default="en")
    abstained = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="text_inferences")


class SelfReportModel(Base):
    """Spec M14 & M15: self_reports table."""
    __tablename__ = "self_reports"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    q1_distress = Column(Integer, nullable=False, default=0)
    q2_safety = Column(Integer, nullable=False, default=0)
    q3_urgency = Column(Integer, nullable=False, default=0)
    q4_can_continue = Column(Integer, nullable=False, default=0)
    support_needs = Column(JSONEncodedType, nullable=False, default=list)
    score = Column(Numeric(5, 2), nullable=False, default=0.0)
    safety_flag = Column(Boolean, nullable=False, default=False)
    completeness = Column(Numeric(4, 3), nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="self_reports")


class ContextResultModel(Base):
    """Spec M16 & M17: context_results table."""
    __tablename__ = "context_results"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    incident_type = Column(String(64), nullable=False, default="unknown")
    ongoing_threat = Column(Boolean, nullable=False, default=False)
    prior_case = Column(Boolean, nullable=False, default=False)
    vulnerability_factors = Column(JSONEncodedType, nullable=False, default=list)
    immediate_support_requested = Column(Boolean, nullable=False, default=False)
    score = Column(Numeric(5, 2), nullable=False, default=0.0)
    completeness = Column(Numeric(4, 3), nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="context_results")


class CrisisResultModel(Base):
    """Spec M13: crisis_results table."""
    __tablename__ = "crisis_results"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    safety_flag = Column(Boolean, nullable=False, default=False)
    crisis_type = Column(String(64), nullable=True)
    confidence = Column(Numeric(4, 3), nullable=False, default=0.0)
    evidence = Column(JSONEncodedType, nullable=False, default=list)
    rule_triggered = Column(Boolean, nullable=False, default=False)
    model_triggered = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="crisis_results")


class RecommendationModel(Base):
    """Spec M24 & M25: recommendations table."""
    __tablename__ = "recommendations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    svi_result_id = Column(GUID, ForeignKey("svi_results.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String(16), nullable=False, default="LOW")
    recommendations = Column(JSONEncodedType, nullable=False, default=list)
    explanation = Column(JSONEncodedType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    session = relationship("SessionModel", back_populates="recommendations")
    svi_result = relationship("SVIResultModel", back_populates="recommendations")


class HumanReviewModel(Base):
    """Spec M26: human_reviews table."""
    __tablename__ = "human_reviews"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    case_id = Column(GUID, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(String(64), nullable=False)
    final_action = Column(String(64), nullable=False)
    modified_priority = Column(String(16), nullable=True)
    reason = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    case = relationship("CaseModel", back_populates="human_reviews")
