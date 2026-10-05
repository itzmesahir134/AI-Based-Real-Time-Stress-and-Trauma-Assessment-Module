"""initial_schema_all_tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-05 00:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. sessions
    op.create_table(
        "sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. consents
    op.create_table(
        "consents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("consent_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. cases
    op.create_table(
        "cases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("assigned_to", sa.String(length=64), nullable=True),
        sa.Column("initial_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. svi_results
    op.create_table(
        "svi_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("svi", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("risk_band", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("evidence_coverage", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("assessment_status", sa.String(length=32), nullable=False),
        sa.Column("safety_override", sa.Boolean(), nullable=False),
        sa.Column("model_config_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 6. audio_assets
    op.create_table(
        "audio_assets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=True),
        sa.Column("case_id", sa.UUID(), nullable=True),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("duration_seconds", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("sample_rate", sa.Integer(), nullable=False),
        sa.Column("channels", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 7. quality_results
    op.create_table(
        "quality_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("quality_score", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("snr_estimate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("clipping_ratio", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("speech_ratio", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("packet_loss", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column("distortion_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 8. transcripts
    op.create_table(
        "transcripts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("quality_id", sa.UUID(), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["quality_id"], ["quality_results.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 9. transcript_segments
    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("transcript_id", sa.UUID(), nullable=False),
        sa.Column("segment_order", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_time", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("end_time", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["transcript_id"], ["transcripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 10. voice_features
    op.create_table(
        "voice_features",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 11. voice_inferences
    op.create_table(
        "voice_inferences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("evidence_features", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("abstained", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 12. text_inferences
    op.create_table(
        "text_inferences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("indicators", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("abstained", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 13. self_reports
    op.create_table(
        "self_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("q1_distress", sa.Integer(), nullable=False),
        sa.Column("q2_safety", sa.Integer(), nullable=False),
        sa.Column("q3_urgency", sa.Integer(), nullable=False),
        sa.Column("q4_can_continue", sa.Integer(), nullable=False),
        sa.Column("support_needs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("safety_flag", sa.Boolean(), nullable=False),
        sa.Column("completeness", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 14. context_results
    op.create_table(
        "context_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("incident_type", sa.String(length=64), nullable=False),
        sa.Column("ongoing_threat", sa.Boolean(), nullable=False),
        sa.Column("prior_case", sa.Boolean(), nullable=False),
        sa.Column("vulnerability_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("immediate_support_requested", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("completeness", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 15. crisis_results
    op.create_table(
        "crisis_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("safety_flag", sa.Boolean(), nullable=False),
        sa.Column("crisis_type", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rule_triggered", sa.Boolean(), nullable=False),
        sa.Column("model_triggered", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 16. recommendations
    op.create_table(
        "recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("svi_result_id", sa.UUID(), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["svi_result_id"], ["svi_results.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 17. human_reviews
    op.create_table(
        "human_reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("reviewer_id", sa.String(length=64), nullable=False),
        sa.Column("final_action", sa.String(length=64), nullable=False),
        sa.Column("modified_priority", sa.String(length=16), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("human_reviews")
    op.drop_table("recommendations")
    op.drop_table("crisis_results")
    op.drop_table("context_results")
    op.drop_table("self_reports")
    op.drop_table("text_inferences")
    op.drop_table("voice_inferences")
    op.drop_table("voice_features")
    op.drop_table("transcript_segments")
    op.drop_table("transcripts")
    op.drop_table("quality_results")
    op.drop_table("audio_assets")
    op.drop_table("audit_logs")
    op.drop_table("svi_results")
    op.drop_table("cases")
    op.drop_table("consents")
    op.drop_table("sessions")
