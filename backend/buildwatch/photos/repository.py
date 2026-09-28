import logging
from datetime import datetime
from typing import Annotated, Sequence

from fastapi import Depends
from sqlalchemy import func, select

from buildwatch.infrastructure.database.helper import SessionDep
from buildwatch.infrastructure.database.models.cv.cv_runs import CVRunsORM
from buildwatch.infrastructure.database.models.cv.detections import DetectionsORM
from buildwatch.infrastructure.database.models.cv.photos import PhotosORM
from buildwatch.photos.contracts import PhotosRepositoryProtocol
from buildwatch.shared.repository import SQLBaseRepository

logger = logging.getLogger(__name__)


class PhotosRepository(SQLBaseRepository, PhotosRepositoryProtocol):
    """Реализация репозитория фотографий"""

    async def create_photo(
        self,
        project_id: int,
        storage_key: str,
        captured_at: datetime | None,
        width: int | None,
        height: int | None,
        format: str | None,
        is_processed: bool = False,
    ) -> int:
        photo = PhotosORM(
            project_id=project_id,
            storage_key=storage_key,
            captured_at=captured_at,
            width=width,
            height=height,
            format=format,
            is_processed=is_processed,
        )
        self.session.add(photo)
        await self.session.flush()
        logger.debug("Photo created id=%d key=%s", photo.id, storage_key)
        return photo.id

    async def get_photo_by_id(self, photo_id: int) -> PhotosORM | None:
        return await self.get_one(PhotosORM, id=photo_id)

    async def list_photos(
        self,
        project_id: int,
        limit: int,
        offset: int,
        is_processed: bool | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> Sequence[PhotosORM]:
        filters = {"project_id": project_id}
        if is_processed is not None:
            filters["is_processed"] = is_processed
        query = select(PhotosORM).filter_by(**filters)
        photo_time = func.coalesce(PhotosORM.captured_at, PhotosORM.created_at)
        if from_dt is not None:
            query = query.where(photo_time >= from_dt)
        if to_dt is not None:
            query = query.where(photo_time < to_dt)
        query = (
            query.order_by(PhotosORM.captured_at.desc().nulls_last())
            .order_by(PhotosORM.created_at.desc())
            .order_by(PhotosORM.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.session.scalars(query)).unique().all())

    async def count_photos(
        self,
        project_id: int,
        is_processed: bool | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(PhotosORM)
            .where(PhotosORM.project_id == project_id)
        )
        if is_processed is not None:
            query = query.where(PhotosORM.is_processed == is_processed)
        photo_time = func.coalesce(PhotosORM.captured_at, PhotosORM.created_at)
        if from_dt is not None:
            query = query.where(photo_time >= from_dt)
        if to_dt is not None:
            query = query.where(photo_time < to_dt)
        return int(await self.session.scalar(query) or 0)

    async def create_cv_run(
        self, photo_id: int, width: int | None, height: int | None, format: str | None
    ) -> int:
        run = CVRunsORM(
            photo_id=photo_id,
            status="pending",
            image_width=width,
            image_height=height,
            image_format=format,
        )
        self.session.add(run)
        await self.session.flush()
        return run.id

    async def lock_cv_run(self, cv_run_id: int) -> CVRunsORM | None:
        return await self.session.scalar(
            select(CVRunsORM).where(CVRunsORM.id == cv_run_id).with_for_update()
        )

    async def active_annotations(self, photos: Sequence[PhotosORM]) -> dict[int, tuple]:
        run_ids = [photo.active_cv_run_id for photo in photos if photo.active_cv_run_id]
        if not run_ids:
            return {}
        runs = (
            await self.session.scalars(
                select(CVRunsORM).where(CVRunsORM.id.in_(run_ids))
            )
        ).all()
        detections = (
            await self.session.scalars(
                select(DetectionsORM)
                .where(DetectionsORM.cv_run_id.in_(run_ids))
                .order_by(DetectionsORM.object_id)
            )
        ).all()
        by_run = {run.id: (run, []) for run in runs}
        for detection in detections:
            by_run[detection.cv_run_id][1].append(detection)
        return by_run

    async def latest_runs(self, photos: Sequence[PhotosORM]) -> dict[int, CVRunsORM]:
        """Load the latest CV run for every photo in one query."""

        photo_ids = [photo.id for photo in photos]
        if not photo_ids:
            return {}
        runs = (
            await self.session.scalars(
                select(CVRunsORM)
                .where(CVRunsORM.photo_id.in_(photo_ids))
                .order_by(
                    CVRunsORM.photo_id,
                    CVRunsORM.created_at.desc(),
                    CVRunsORM.id.desc(),
                )
            )
        ).all()
        latest: dict[int, CVRunsORM] = {}
        for run in runs:
            latest.setdefault(run.photo_id, run)
        return latest

    async def save_cv_success(self, run: CVRunsORM, result) -> None:
        from datetime import datetime, timezone

        run.status = "succeeded"
        run.model_name = result.processing.model.name
        run.model_version = result.processing.model.version
        run.model_storage_weights = result.processing.model.storage_weights
        run.inference_ms = result.processing.inference_ms
        run.image_width = result.image_info.width
        run.image_height = result.image_info.height
        run.image_format = result.image_info.format
        run.completed_at = datetime.now(timezone.utc)
        self.session.add_all(
            DetectionsORM(
                cv_run_id=run.id,
                object_id=item.object_id,
                class_id=item.class_id,
                class_name=item.class_name,
                detection_confidence=item.confidence.detection,
                activity_confidence=item.confidence.activity,
                activity_state=item.confidence.activity_state,
                x_center=item.bbox.x_center,
                y_center=item.bbox.y_center,
                w=item.bbox.w,
                h=item.bbox.h,
            )
            for item in result.detections
        )
        await self.session.flush()

    async def activate_cv_run(self, photo_id: int, cv_run_id: int) -> None:
        photo = await self.session.scalar(
            select(PhotosORM).where(PhotosORM.id == photo_id).with_for_update()
        )
        if photo is None:
            raise ValueError(f"Photo {photo_id} does not exist")
        if photo.active_cv_run_id is None or cv_run_id >= photo.active_cv_run_id:
            photo.active_cv_run_id = cv_run_id
            photo.is_processed = True
            await self.session.flush()

    async def set_processed(self, photo_id: int, is_processed: bool) -> bool:
        photo = await self.get_one(PhotosORM, id=photo_id)
        if photo is None:
            return False
        photo.is_processed = is_processed
        await self.session.flush()
        return True


def get_photos_repository(session: SessionDep) -> PhotosRepositoryProtocol:
    return PhotosRepository(session)


PhotosRepositoryDep = Annotated[PhotosRepository, Depends(get_photos_repository)]
