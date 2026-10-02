import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import TypeDecorator, CHAR

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


class SessionModel(Base):
    """Spec §23: sessions table."""
    __tablename__ = "sessions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    channel = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="INITIALIZED")
    language = Column(String(32), nullable=True, default="hi")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime(timezone=True), nullable=True)

    consents = relationship("ConsentModel", back_populates="session", cascade="all, delete-orphan")
    cases = relationship("CaseModel", back_populates="session", cascade="all, delete-orphan")
    svi_results = relationship("SVIResultModel", back_populates="session", cascade="all, delete-orphan")


class ConsentModel(Base):
    """Spec §22: consents table."""
    __tablename__ = "consents"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    session_id = Column(GUID, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    consent_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    notes = Column(Text, nullable=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

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
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    session = relationship("SessionModel", back_populates="cases")


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
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    session = relationship("SessionModel", back_populates="svi_results")


class AuditLogModel(Base):
    """Spec §22, §39: audit_logs table."""
    __tablename__ = "audit_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
