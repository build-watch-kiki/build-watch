"""add CV runs and detections

Revision ID: 2e9a5d0f7b31
Revises: 9f2d6b7a4c31
Create Date: 2026-09-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2e9a5d0f7b31"
down_revision: Union[str, Sequence[str], None] = "9f2d6b7a4c31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cv_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("photo_id", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=32), server_default="pending", nullable=False
        ),
        sa.Column("model_name", sa.String(length=127), nullable=True),
        sa.Column("model_version", sa.String(length=127), nullable=True),
        sa.Column("model_storage_weights", sa.String(length=512), nullable=True),
        sa.Column("inference_ms", sa.Integer(), nullable=True),
        sa.Column("image_width", sa.Integer(), nullable=True),
        sa.Column("image_height", sa.Integer(), nullable=True),
        sa.Column("image_format", sa.String(length=16), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')", name="ck_cv_runs_status"
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "preview_render_enqueued_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["photo_id"], ["photos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cv_runs_photo_created", "cv_runs", ["photo_id", "created_at"])
    op.add_column(
        "photos", sa.Column("preview_storage_key", sa.String(length=512), nullable=True)
    )
    op.execute("UPDATE photos SET is_processed = false WHERE is_processed = true")
    op.add_column("photos", sa.Column("preview_cv_run_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_photos_preview_cv_run_id",
        "photos",
        "cv_runs",
        ["preview_cv_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "detections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cv_run_id", sa.Integer(), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("class_name", sa.String(length=127), nullable=False),
        sa.Column("detection_confidence", sa.Float(), nullable=False),
        sa.Column("activity_confidence", sa.Float(), nullable=True),
        sa.Column("activity_state", sa.String(length=32), nullable=True),
        sa.Column("x_center", sa.Float(), nullable=False),
        sa.Column("y_center", sa.Float(), nullable=False),
        sa.Column("w", sa.Float(), nullable=False),
        sa.Column("h", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cv_run_id"], ["cv_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cv_run_id", "object_id", name="uq_detections_run_object"),
        sa.CheckConstraint("object_id >= 0", name="ck_detections_object_id_positive"),
        sa.CheckConstraint(
            "detection_confidence >= 0 AND detection_confidence <= 1",
            name="ck_detections_detection_confidence_range",
        ),
        sa.CheckConstraint(
            "activity_confidence IS NULL OR "
            "(activity_confidence >= 0 AND activity_confidence <= 1)",
            name="ck_detections_activity_confidence_range",
        ),
        sa.CheckConstraint("w >= 0", name="ck_detections_width_positive"),
        sa.CheckConstraint("h >= 0", name="ck_detections_height_positive"),
    )
    op.create_index("ix_detections_cv_run", "detections", ["cv_run_id"])


def downgrade() -> None:
    op.drop_index("ix_detections_cv_run", table_name="detections")
    op.drop_table("detections")
    op.drop_constraint("fk_photos_preview_cv_run_id", "photos", type_="foreignkey")
    op.drop_column("photos", "preview_cv_run_id")
    op.drop_column("photos", "preview_storage_key")
    op.drop_index("ix_cv_runs_photo_created", table_name="cv_runs")
    op.drop_table("cv_runs")
