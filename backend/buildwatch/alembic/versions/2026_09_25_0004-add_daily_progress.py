"""Add daily plan-fact progress and evidence.

Revision ID: 7d3a8f2c5e91
Revises: 6c2f9e1a4d70
"""

from alembic import op
import sqlalchemy as sa

revision = "7d3a8f2c5e91"
down_revision = "6c2f9e1a4d70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "daily_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("outcome", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=127), nullable=True),
        sa.Column("previous_stage_id", sa.Integer(), nullable=True),
        sa.Column("next_stage_id", sa.Integer(), nullable=True),
        sa.Column("actual_stage_id", sa.Integer(), nullable=True),
        sa.Column("previous_stage_name", sa.String(length=255), nullable=True),
        sa.Column("next_stage_name", sa.String(length=255), nullable=True),
        sa.Column("actual_stage_name", sa.String(length=255), nullable=True),
        sa.Column("previous_score", sa.Float(), nullable=True),
        sa.Column("next_score", sa.Float(), nullable=True),
        sa.Column("stage_changed", sa.Boolean(), nullable=False),
        sa.Column("has_quantity_deviation", sa.Boolean(), nullable=False),
        sa.Column("timing_status", sa.String(length=32), nullable=False),
        sa.Column("time_deviation_days", sa.Integer(), nullable=True),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("usable_observation_count", sa.Integer(), nullable=False),
        sa.Column("processing_coverage", sa.Float(), nullable=False),
        sa.Column("agreement_rate", sa.Float(), nullable=False),
        sa.Column("data_quality", sa.String(length=32), nullable=False),
        sa.Column("data_quality_reasons", sa.JSON(), nullable=False),
        sa.Column("unknown_detection_count", sa.Integer(), nullable=False),
        sa.Column("unknown_classes", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "outcome IN ('previous_without_deviation', "
            "'previous_with_deviation', 'next_without_deviation', "
            "'next_with_deviation', 'insufficient_data')",
            name="ck_daily_progress_outcome",
        ),
        sa.CheckConstraint(
            "data_quality IN ('high', 'medium', 'low', 'insufficient')",
            name="ck_daily_progress_data_quality",
        ),
        sa.CheckConstraint(
            "timing_status IN ('on_schedule', 'early', 'late', 'unknown')",
            name="ck_daily_progress_timing_status",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["previous_stage_id"], ["stages.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["next_stage_id"], ["stages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["actual_stage_id"], ["stages.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "analysis_date", name="uq_daily_progress_project_date"
        ),
    )
    op.create_table(
        "daily_progress_techniques",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("progress_id", sa.Integer(), nullable=False),
        sa.Column("technique_id", sa.Integer(), nullable=True),
        sa.Column("technique_name", sa.String(length=127), nullable=False),
        sa.Column("technique_name_ru", sa.String(length=127), nullable=False),
        sa.Column("planned_quantity", sa.Integer(), nullable=False),
        sa.Column("actual_quantity", sa.Integer(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("tolerance", sa.Integer(), nullable=False),
        sa.Column("is_deviation", sa.Boolean(), nullable=False),
        sa.Column("deviation_type", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "deviation_type IN ('none', 'missing', 'unexpected', "
            "'quantity_mismatch')",
            name="ck_daily_progress_technique_deviation_type",
        ),
        sa.ForeignKeyConstraint(
            ["progress_id"], ["daily_progress.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["technique_id"], ["techniques.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "progress_id", "technique_id", name="uq_daily_progress_technique"
        ),
    )
    op.create_table(
        "daily_progress_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("progress_id", sa.Integer(), nullable=False),
        sa.Column("photo_id", sa.Integer(), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["progress_id"], ["daily_progress.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["photo_id"], ["photos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "progress_id", "photo_id", name="uq_daily_progress_evidence_photo"
        ),
    )


def downgrade() -> None:
    op.drop_table("daily_progress_evidence")
    op.drop_table("daily_progress_techniques")
    op.drop_table("daily_progress")
