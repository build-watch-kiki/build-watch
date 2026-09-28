from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from buildwatch.infrastructure.database.models.base import Base
from buildwatch.infrastructure.database.models.mixins import (
    CreatedAtMixin,
    UpdatedAtMixin,
)


class PhotosORM(Base, CreatedAtMixin, UpdatedAtMixin):
    """Фотография стройплощадки, привязанная к проекту"""

    __tablename__ = "photos"
    __table_args__ = (Index("ix_photos_project_captured", "project_id", "captured_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    width: Mapped[int | None]
    height: Mapped[int | None]
    format: Mapped[str | None] = mapped_column(String(16))
    is_processed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    active_cv_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("cv_runs.id", ondelete="SET NULL")
    )

    # project: Mapped[ProjectsORM] = relationship(lazy="joined")
