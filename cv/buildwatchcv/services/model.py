import asyncio
import io
import logging
import time
from functools import lru_cache
from pathlib import Path

from buildwatchcv.infrastructure.minio_client import get_s3_client
from buildwatchcv.settings import get_settings

logger = logging.getLogger(__name__)

CACHE_DIR = Path("/tmp/models")


@lru_cache(maxsize=8)
def _load_yolo_cached(weights_path: str):
    """Кэшированная загрузка YOLO. Вызывается в to_thread."""
    try:
        from ultralytics import YOLO  # type: ignore
    except ModuleNotFoundError as e:
        raise RuntimeError("ultralytics is not installed") from e
    logger.info("loading YOLO weights %s", weights_path)
    return YOLO(weights_path)


async def _ensure_weights(version: str) -> Path:
    """Скачать best.pt версии если нет в кэше. Версия — имя папки: v1, v2-2026-09-24."""
    settings = get_settings()
    s3 = get_s3_client()
    bucket = settings.s3.cv_bucket
    key = s3.weights_key(version, "best.pt")
    local = CACHE_DIR / version / "best.pt"

    if local.exists():
        logger.info("weights cache hit %s -> %s", version, local)
        return local

    logger.info("downloading weights s3://%s/%s -> %s", bucket, key, local)
    try:
        await asyncio.to_thread(s3.download_to_file, bucket, key, local)
    except Exception as e:
        raise RuntimeError(
            f"unable to download weights s3://{bucket}/{key} version={version}"
        ) from e
    return local


async def warmup() -> None:
    """Загрузить и инициализировать модель настроенной версии до приёма фото."""
    version = get_settings().s3.model_version.strip().strip("/")
    try:
        local = await _ensure_weights(version)
        await asyncio.to_thread(_load_yolo_cached, str(local))
    except Exception:
        logger.warning("model warmup failed for version=%s", version, exc_info=True)
    else:
        logger.info("model warmup complete for version=%s", version)


async def predict(image_bytes: bytes, version: str | None = None) -> tuple[list, int]:
    """Запуск инференса. Возвращает (raw_results, inference_ms)."""
    settings = get_settings()
    version = (version or settings.s3.model_version).strip().strip("/")

    local = await _ensure_weights(version)
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    def _run():
        model = _load_yolo_cached(str(local))
        t0 = time.perf_counter()
        results = model(img, verbose=False)
        dt = int((time.perf_counter() - t0) * 1000)
        return results, dt

    results, inference_ms = await asyncio.to_thread(_run)
    logger.info("yolo inference version=%s ms=%d", version, inference_ms)
    return results, inference_ms
