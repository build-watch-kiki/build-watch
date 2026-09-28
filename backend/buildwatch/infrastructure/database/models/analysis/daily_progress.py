from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from buildwatch.infrastructure.database.models.base import Base
from buildwatch.infrastructure.database.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from buildwatch.infrastructure.database.models.cv.photos import PhotosORM


class DailyProgressORM(Base, CreatedAtMixin):
    """Суточный результат сопоставления фактической техники с планом."""

    __tablename__ = "daily_progress"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "analysis_date", name="uq_daily_progress_project_date"
        ),
        CheckConstraint(
            "outcome IN ("
            "'previous_without_deviation', "
            "'previous_with_deviation', "
            "'next_without_deviation', "
            "'next_with_deviation', "
            "'insufficient_data')",
            name="ck_daily_progress_outcome",
        ),
        CheckConstraint(
            "data_quality IN ('high', 'medium', 'low', 'insufficient')",
            name="ck_daily_progress_data_quality",
        ),
        CheckConstraint(
            "timing_status IN ('on_schedule', 'early', 'late', 'unknown')",
            name="ck_daily_progress_timing_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(127))

    previous_stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("stages.id", ondelete="SET NULL")
    )
    next_stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("stages.id", ondelete="SET NULL")
    )
    actual_stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("stages.id", ondelete="SET NULL")
    )
    previous_stage_name: Mapped[str | None] = mapped_column(String(255))
    next_stage_name: Mapped[str | None] = mapped_column(String(255))
    actual_stage_name: Mapped[str | None] = mapped_column(String(255))
    previous_score: Mapped[float | None] = mapped_column(Float)
    next_score: Mapped[float | None] = mapped_column(Float)
    stage_changed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_quantity_deviation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    timing_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unknown"
    )
    time_deviation_days: Mapped[int | None] = mapped_column(Integer)

    observation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usable_observation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    processing_coverage: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    agreement_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    data_quality: Mapped[str] = mapped_column(
        String(32), nullable=False, default="insufficient"
    )
    data_quality_reasons: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    unknown_detection_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    unknown_classes: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    techniques: Mapped[list["DailyProgressTechniqueORM"]] = relationship(
        back_populates="progress", cascade="all, delete-orphan", lazy="selectin"
    )
    evidence: Mapped[list["DailyProgressEvidenceORM"]] = relationship(
        back_populates="progress", cascade="all, delete-orphan", lazy="selectin"
    )


class DailyProgressTechniqueORM(Base):
    """План-факт одного вида техники в суточном результате."""

    __tablename__ = "daily_progress_techniques"
    __table_args__ = (
        UniqueConstraint(
            "progress_id", "technique_id", name="uq_daily_progress_technique"
        ),
        CheckConstraint(
            "deviation_type IN ('none', 'missing', 'unexpected', 'quantity_mismatch')",
            name="ck_daily_progress_technique_deviation_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    progress_id: Mapped[int] = mapped_column(
        ForeignKey("daily_progress.id", ondelete="CASCADE"), nullable=False
    )
    technique_id: Mapped[int | None] = mapped_column(
        ForeignKey("techniques.id", ondelete="SET NULL")
    )
    technique_name: Mapped[str] = mapped_column(String(127), nullable=False)
    technique_name_ru: Mapped[str] = mapped_column(String(127), nullable=False)
    planned_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    tolerance: Mapped[int] = mapped_column(Integer, nullable=False)
    is_deviation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    deviation_type: Mapped[str] = mapped_column(String(32), nullable=False)

    progress: Mapped[DailyProgressORM] = relationship(back_populates="techniques")


class DailyProgressEvidenceORM(Base):
    """Фотография, объясняющая суточный результат или предупреждение."""

    __tablename__ = "daily_progress_evidence"
    __table_args__ = (
        UniqueConstraint(
            "progress_id", "photo_id", name="uq_daily_progress_evidence_photo"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    progress_id: Mapped[int] = mapped_column(
        ForeignKey("daily_progress.id", ondelete="CASCADE"), nullable=False
    )
    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photos.id", ondelete="CASCADE"), nullable=False
    )
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    progress: Mapped[DailyProgressORM] = relationship(back_populates="evidence")
    photo: Mapped["PhotosORM"] = relationship(lazy="joined")
