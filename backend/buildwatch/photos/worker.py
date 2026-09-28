"""RabbitMQ consumer for CV results."""

import logging
from datetime import datetime, timezone

from buildwatch.infrastructure.broker import CV_RESULT_QUEUE, broker
from buildwatch.infrastructure.database.helper import db_helper
from buildwatch.photos.repository import PhotosRepository
from buildwatch.photos.schemas import CVResultMessage
from buildwatch.progress.analyzer import DailyProgressAnalyzer
from buildwatch.progress.repository import ProgressRepository
from buildwatch.settings import get_settings

logger = logging.getLogger(__name__)


async def process_cv_result(
    message: CVResultMessage, repo: PhotosRepository, commit, recalculate=None
) -> bool:
    """Persist a CV result once and activate successful detections atomically."""
    run = await repo.lock_cv_run(message.cv_run_id)
    if run is None:
        raise ValueError(f"Unknown CV run {message.cv_run_id}")
    if run.status != "pending":
        return False
    if message.status == "failed":
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        await commit()
        logger.warning("CV run %d failed: %s", run.id, message.error)
        return False
    if message.result is None:
        raise ValueError("Successful CV result is missing result")
    photo = await repo.get_photo_by_id(run.photo_id)
    if photo is None or message.result.image_info.key != photo.storage_key:
        raise ValueError(f"CV result image key does not match run {run.id}")
    await repo.save_cv_success(run, message.result)
    await repo.activate_cv_run(run.photo_id, run.id)
    if recalculate is not None:
        await recalculate(photo)
    await commit()
    return True


async def consume_cv_result(message: CVResultMessage) -> None:
    async with db_helper.session_maker() as session:
        repo = PhotosRepository(session)
        analyzer = DailyProgressAnalyzer(
            ProgressRepository(session), get_settings().analysis
        )

        async def recalculate(photo) -> None:
            captured_at = photo.captured_at or photo.created_at
            await analyzer.recalculate_from(
                photo.project_id, analyzer.analysis_date_for(captured_at)
            )

        try:
            await process_cv_result(
                message, repo, session.commit, recalculate=recalculate
            )
        except Exception:
            await session.rollback()
            raise


@broker.subscriber(CV_RESULT_QUEUE)
async def handle_cv_result(message: CVResultMessage) -> None:
    await consume_cv_result(message)
