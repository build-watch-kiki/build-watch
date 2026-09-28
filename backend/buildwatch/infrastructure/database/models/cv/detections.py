from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from buildwatch.infrastructure.database.models.base import Base
from buildwatch.infrastructure.database.models.mixins import CreatedAtMixin


class DetectionsORM(Base, CreatedAtMixin):
    """Результат обнаружения объекта в рамках одного CV-запуска."""

    __tablename__ = "detections"
    __table_args__ = (
        Index("ix_detections_cv_run", "cv_run_id"),
        UniqueConstraint("cv_run_id", "object_id", name="uq_detections_run_object"),
        CheckConstraint("object_id >= 0", name="ck_detections_object_id_positive"),
        CheckConstraint(
            "detection_confidence >= 0 AND detection_confidence <= 1",
            name="ck_detections_detection_confidence_range",
        ),
        CheckConstraint(
            "activity_confidence IS NULL OR "
            "(activity_confidence >= 0 AND activity_confidence <= 1)",
            name="ck_detections_activity_confidence_range",
        ),
        CheckConstraint("w >= 0", name="ck_detections_width_positive"),
        CheckConstraint("h >= 0", name="ck_detections_height_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cv_run_id: Mapped[int] = mapped_column(
        ForeignKey("cv_runs.id", ondelete="CASCADE"), nullable=False
    )
    object_id: Mapped[int] = mapped_column(nullable=False)
    class_id: Mapped[int] = mapped_column(nullable=False)
    class_name: Mapped[str] = mapped_column(String(127), nullable=False)
    detection_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    activity_confidence: Mapped[float | None] = mapped_column(Float)
    activity_state: Mapped[str | None] = mapped_column(String(32))
    x_center: Mapped[float] = mapped_column(Float, nullable=False)
    y_center: Mapped[float] = mapped_column(Float, nullable=False)
    w: Mapped[float] = mapped_column(Float, nullable=False)
    h: Mapped[float] = mapped_column(Float, nullable=False)
