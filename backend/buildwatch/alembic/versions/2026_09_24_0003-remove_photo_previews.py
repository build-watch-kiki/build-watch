"""Use CV detections without rendered photo previews.

Revision ID: 6c2f9e1a4d70
Revises: 2e9a5d0f7b31
"""

from alembic import op
import sqlalchemy as sa

revision = "6c2f9e1a4d70"
down_revision = "2e9a5d0f7b31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("fk_photos_preview_cv_run_id", "photos", type_="foreignkey")
    op.alter_column("photos", "preview_cv_run_id", new_column_name="active_cv_run_id")
    op.create_foreign_key(
        "fk_photos_active_cv_run_id",
        "photos",
        "cv_runs",
        ["active_cv_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # A successful CV run may have been persisted before preview rendering failed.
    # Prefer the newest successful run for every photo, including those cases.
    op.execute("""
        UPDATE photos AS photo
        SET active_cv_run_id = latest.cv_run_id,
            is_processed = latest.cv_run_id IS NOT NULL
        FROM (
            SELECT photo_id, MAX(id) AS cv_run_id
            FROM cv_runs
            WHERE status = 'succeeded'
            GROUP BY photo_id
        ) AS latest
        WHERE photo.id = latest.photo_id
        """)
    op.execute(
        "UPDATE photos SET active_cv_run_id = NULL, is_processed = false "
        "WHERE active_cv_run_id IS NULL"
    )
    op.drop_column("photos", "preview_storage_key")
    op.drop_column("cv_runs", "preview_render_enqueued_at")


def downgrade() -> None:
    op.add_column(
        "cv_runs", sa.Column("preview_render_enqueued_at", sa.DateTime(timezone=True))
    )
    op.add_column("photos", sa.Column("preview_storage_key", sa.String(512)))
    op.drop_constraint("fk_photos_active_cv_run_id", "photos", type_="foreignkey")
    op.alter_column("photos", "active_cv_run_id", new_column_name="preview_cv_run_id")
    op.create_foreign_key(
        "fk_photos_preview_cv_run_id",
        "photos",
        "cv_runs",
        ["preview_cv_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
