import asyncio
import logging

from buildwatchcv.messages import PhotoUploadedMessage
from buildwatchcv.schemas.response import DetectionResponse
from buildwatchcv.services.mapper import build_response
from buildwatchcv.services.model import predict
from buildwatchcv.services.photo_loader import load_photo
from buildwatchcv.settings import get_settings

logger = logging.getLogger(__name__)


async def run_pipeline(msg: PhotoUploadedMessage) -> DetectionResponse:
    """Полный пайплайн: S3 фото -> инференс (кэш весов по версии) -> DetectionResponse."""
    # 1. фото
    data, width, height, fmt = await load_photo(
        msg.object_path,
        fallback_width=msg.width,
        fallback_height=msg.height,
        fallback_format=msg.format,
    )

    # используем размеры из сообщения, если PIL не смог
    if msg.width and msg.height:
        # доверяем детекту, но оставляем то, что нашли
        pass

    # 2. инференс (веса качаются по версии из S3 settings)
    yolo_results, inference_ms = await predict(data)

    # 3. сборка ответа с путём до использованной версии весов
    response = build_response(msg, width, height, fmt, yolo_results, inference_ms)

    # 4. TEMP-DEBUG: локальный дамп (удалить перед продом). Ошибки дампа
    # не должны ломать основной ответ в брокер.
    try:
        out_cfg = get_settings().output
        if out_cfg.enabled:
            from buildwatchcv.services.annotate import draw_boxes
            from buildwatchcv.services.debug_dump import save_debug_run

            annotated = await asyncio.to_thread(draw_boxes, data, response.detections)
            folder = await asyncio.to_thread(
                save_debug_run,
                out_cfg.resolved_dir,
                response.processing.model.version,
                msg.object_path,
                data,
                annotated,
                response,
            )
            logger.info("debug dump %s -> %s", msg.object_path, folder)
    except Exception:
        logger.warning("debug dump failed for %s", msg.object_path, exc_info=True)

    logger.info(
        "pipeline done key=%s version=%s detections=%d ms=%d",
        msg.object_path,
        response.processing.model.version,
        len(response.detections),
        inference_ms,
    )
    return response
