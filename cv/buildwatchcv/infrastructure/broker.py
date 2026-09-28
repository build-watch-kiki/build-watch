import logging

from faststream.rabbit import RabbitBroker, RabbitQueue

from buildwatchcv.messages import PhotoUploadedMessage
from buildwatchcv.schemas.cv_result import CvSucceededEnvelope, CvFailedEnvelope
from buildwatchcv.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

NEW_PHOTO_QUEUE = RabbitQueue(settings.broker.queue.new_photos, durable=True)
CV_RESULT_QUEUE = RabbitQueue(settings.broker.queue.cv_result, durable=True)
broker = RabbitBroker(settings.broker.RABBITMQ_DSN)


@broker.subscriber(NEW_PHOTO_QUEUE)
async def handle_photo_uploaded(message: PhotoUploadedMessage) -> None:
    """Обрабатывает фото и публикует результат CV в очередь cv-result."""
    from buildwatchcv.services.pipeline import run_pipeline

    logger.info("new-photo cv_run_id=%s %s", message.cv_run_id, message.object_path)
    try:
        response = await run_pipeline(message)
        envelope = CvSucceededEnvelope(cv_run_id=message.cv_run_id, result=response)
    except Exception as exc:
        logger.exception("failed cv_run_id=%s %s", message.cv_run_id, message.object_path)
        failed = CvFailedEnvelope(cv_run_id=message.cv_run_id, error=f"{type(exc).__name__}: {exc}"[:2000])
        await broker.publish(
            failed.model_dump(mode="json"),
            queue=CV_RESULT_QUEUE,
            mandatory=True,
            persist=True,
        )
        return
    await broker.publish(
        envelope.model_dump(mode="json"),
        queue=CV_RESULT_QUEUE,
        mandatory=True,
        persist=True,
    )
    logger.info("published succeeded cv_run_id=%s", message.cv_run_id)
