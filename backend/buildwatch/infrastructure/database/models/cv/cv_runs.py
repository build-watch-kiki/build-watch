from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from buildwatch.infrastructure.database.models.base import Base
from buildwatch.infrastructure.database.models.mixins import CreatedAtMixin


class CVRunsORM(Base, CreatedAtMixin):
    """Один запуск CV для фотографии."""

    __tablename__ = "cv_runs"
    __table_args__ = (
        Index("ix_cv_runs_photo_created", "photo_id", "created_at"),
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')", name="ck_cv_runs_status"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photos.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default="pending", server_default="pending", nullable=False
    )
    model_name: Mapped[str | None] = mapped_column(String(127))
    model_version: Mapped[str | None] = mapped_column(String(127))
    model_storage_weights: Mapped[str | None] = mapped_column(String(512))
    inference_ms: Mapped[int | None] = mapped_column(Integer)
    image_width: Mapped[int | None] = mapped_column(Integer)
    image_height: Mapped[int | None] = mapped_column(Integer)
    image_format: Mapped[str | None] = mapped_column(String(16))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
