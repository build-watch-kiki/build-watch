from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Annotated, Sequence

from fastapi import Depends
from sqlalchemy import delete, exists, func, select
from sqlalchemy.orm import aliased, selectinload

from buildwatch.infrastructure.database.helper import SessionDep
from buildwatch.infrastructure.database.models import (
    CVRunsORM,
    DailyProgressEvidenceORM,
    DailyProgressORM,
    DailyProgressTechniqueORM,
    DetectionsORM,
    PhotosORM,
    ProjectsORM,
    StagesORM,
    TechniquesORM,
)
from buildwatch.infrastructure.database.models.core.techniques import StageTechniquesORM


@dataclass(slots=True)
class PhotoObservation:
    photo_id: int
    storage_key: str
    captured_at: datetime
    detections: list[tuple[str, float]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class GanttProgressSnapshot:
    stage_id: int
    start_date: date
    end_date: date
    progress: DailyProgressORM


class ProgressRepository:
    def __init__(self, session):
        self.session = session

    async def lock_project(self, project_id: int) -> ProjectsORM | None:
        return await self.session.scalar(
            select(ProjectsORM)
            .where(ProjectsORM.id == project_id)
            .with_for_update(of=ProjectsORM)
        )

    @staticmethod
    def _photo_time():
        return func.coalesce(PhotosORM.captured_at, PhotosORM.created_at)

    async def count_observations(
        self, project_id: int, start: datetime, end: datetime
    ) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(PhotosORM)
                .where(
                    PhotosORM.project_id == project_id,
                    self._photo_time() >= start,
                    self._photo_time() < end,
                )
            )
            or 0
        )

    async def load_observations(
        self, project_id: int, start: datetime, end: datetime
    ) -> list[PhotoObservation]:
        rows = (
            await self.session.execute(
                select(
                    PhotosORM.id,
                    PhotosORM.storage_key,
                    self._photo_time().label("captured_at"),
                    DetectionsORM.class_name,
                    DetectionsORM.detection_confidence,
                )
                .join(CVRunsORM, CVRunsORM.id == PhotosORM.active_cv_run_id)
                .outerjoin(DetectionsORM, DetectionsORM.cv_run_id == CVRunsORM.id)
                .where(
                    PhotosORM.project_id == project_id,
                    CVRunsORM.status == "succeeded",
                    self._photo_time() >= start,
                    self._photo_time() < end,
                )
                .order_by(PhotosORM.id, DetectionsORM.object_id)
            )
        ).all()
        by_photo: dict[int, PhotoObservation] = {}
        for row in rows:
            observation = by_photo.setdefault(
                row.id,
                PhotoObservation(
                    photo_id=row.id,
                    storage_key=row.storage_key,
                    captured_at=row.captured_at,
                ),
            )
            if row.class_name is not None:
                observation.detections.append(
                    (row.class_name, row.detection_confidence)
                )
        return list(by_photo.values())

    async def load_techniques(self) -> Sequence[TechniquesORM]:
        return (
            await self.session.scalars(select(TechniquesORM).order_by(TechniquesORM.id))
        ).all()

    async def load_stages(self, project_id: int) -> Sequence[StagesORM]:
        return (
            (
                await self.session.scalars(
                    select(StagesORM)
                    .where(StagesORM.project_id == project_id)
                    .options(
                        selectinload(StagesORM.technique_links).joinedload(
                            StageTechniquesORM.technique
                        )
                    )
                    .order_by(StagesORM.start_dt, StagesORM.end_dt, StagesORM.id)
                )
            )
            .unique()
            .all()
        )

    async def last_actual_progress(
        self, project_id: int, before_date: date
    ) -> DailyProgressORM | None:
        return await self.session.scalar(
            select(DailyProgressORM)
            .where(
                DailyProgressORM.project_id == project_id,
                DailyProgressORM.analysis_date < before_date,
                DailyProgressORM.actual_stage_id.is_not(None),
                DailyProgressORM.outcome != "insufficient_data",
            )
            .order_by(DailyProgressORM.analysis_date.desc())
            .limit(1)
        )

    async def upsert_progress(
        self,
        project_id: int,
        analysis_date: date,
        values: dict,
        technique_rows: Sequence[DailyProgressTechniqueORM],
        evidence_rows: Sequence[DailyProgressEvidenceORM],
    ) -> DailyProgressORM:
        progress = await self.session.scalar(
            select(DailyProgressORM).where(
                DailyProgressORM.project_id == project_id,
                DailyProgressORM.analysis_date == analysis_date,
            )
        )
        if progress is None:
            progress = DailyProgressORM(
                project_id=project_id, analysis_date=analysis_date, **values
            )
            self.session.add(progress)
            await self.session.flush()
        else:
            for key, value in values.items():
                setattr(progress, key, value)
            await self.session.execute(
                delete(DailyProgressTechniqueORM).where(
                    DailyProgressTechniqueORM.progress_id == progress.id
                )
            )
            await self.session.execute(
                delete(DailyProgressEvidenceORM).where(
                    DailyProgressEvidenceORM.progress_id == progress.id
                )
            )
        for row in technique_rows:
            row.progress_id = progress.id
            self.session.add(row)
        for row in evidence_rows:
            row.progress_id = progress.id
            self.session.add(row)
        await self.session.flush()
        return progress

    async def list_progress(
        self, project_id: int, from_date: date | None, to_date: date | None
    ) -> Sequence[DailyProgressORM]:
        query = (
            select(DailyProgressORM)
            .where(DailyProgressORM.project_id == project_id)
            .options(selectinload(DailyProgressORM.techniques))
            .order_by(DailyProgressORM.analysis_date.desc())
        )
        if from_date is not None:
            query = query.where(DailyProgressORM.analysis_date >= from_date)
        if to_date is not None:
            query = query.where(DailyProgressORM.analysis_date <= to_date)
        return (await self.session.scalars(query)).unique().all()

    async def get_progress_day(
        self, project_id: int, analysis_date: date
    ) -> DailyProgressORM | None:
        return await self.session.scalar(
            select(DailyProgressORM)
            .where(
                DailyProgressORM.project_id == project_id,
                DailyProgressORM.analysis_date == analysis_date,
            )
            .options(
                selectinload(DailyProgressORM.techniques),
                selectinload(DailyProgressORM.evidence).joinedload(
                    DailyProgressEvidenceORM.photo
                ),
            )
        )

    async def list_gantt_progress(
        self, project_id: int, from_date: date | None, to_date: date | None
    ) -> list[GanttProgressSnapshot]:
        child = aliased(StagesORM)
        filters = [
            DailyProgressORM.project_id == project_id,
            DailyProgressORM.actual_stage_id.is_not(None),
            ~exists(select(child.id).where(child.parent_id == StagesORM.id)),
        ]
        if from_date is not None:
            filters.append(DailyProgressORM.analysis_date >= from_date)
        if to_date is not None:
            filters.append(DailyProgressORM.analysis_date <= to_date)

        periods_query = (
            select(
                DailyProgressORM.actual_stage_id.label("stage_id"),
                func.min(DailyProgressORM.analysis_date).label("start_date"),
                func.max(DailyProgressORM.analysis_date).label("end_date"),
            )
            .join(StagesORM, StagesORM.id == DailyProgressORM.actual_stage_id)
            .where(*filters)
            .group_by(DailyProgressORM.actual_stage_id)
            .order_by(func.min(DailyProgressORM.analysis_date))
        )
        periods = (await self.session.execute(periods_query)).all()
        if not periods:
            return []

        latest_dates = (
            select(
                DailyProgressORM.actual_stage_id.label("stage_id"),
                func.max(DailyProgressORM.analysis_date).label("analysis_date"),
            )
            .join(StagesORM, StagesORM.id == DailyProgressORM.actual_stage_id)
            .where(*filters)
            .group_by(DailyProgressORM.actual_stage_id)
            .subquery()
        )
        latest_query = (
            select(DailyProgressORM)
            .join(
                latest_dates,
                (latest_dates.c.stage_id == DailyProgressORM.actual_stage_id)
                & (latest_dates.c.analysis_date == DailyProgressORM.analysis_date),
            )
            .options(selectinload(DailyProgressORM.techniques))
        )
        latest = {
            item.actual_stage_id: item
            for item in (await self.session.scalars(latest_query)).unique().all()
        }
        return [
            GanttProgressSnapshot(
                stage_id=row.stage_id,
                start_date=row.start_date,
                end_date=row.end_date,
                progress=latest[row.stage_id],
            )
            for row in periods
            if row.stage_id in latest
        ]

    async def list_progress_dates(
        self, project_id: int, from_date: date | None = None
    ) -> Sequence[date]:
        query = select(DailyProgressORM.analysis_date).where(
            DailyProgressORM.project_id == project_id
        )
        if from_date is not None:
            query = query.where(DailyProgressORM.analysis_date >= from_date)
        return (
            await self.session.scalars(query.order_by(DailyProgressORM.analysis_date))
        ).all()

    async def list_processed_photo_times(self) -> Sequence[tuple[int, datetime]]:
        return (
            await self.session.execute(
                select(PhotosORM.project_id, self._photo_time())
                .join(CVRunsORM, CVRunsORM.id == PhotosORM.active_cv_run_id)
                .where(CVRunsORM.status == "succeeded")
                .order_by(PhotosORM.project_id, self._photo_time())
            )
        ).all()


def get_progress_repository(session: SessionDep) -> ProgressRepository:
    return ProgressRepository(session)


ProgressRepositoryDep = Annotated[ProgressRepository, Depends(get_progress_repository)]
