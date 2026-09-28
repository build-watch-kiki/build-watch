import asyncio
import io
import logging
from pathlib import Path

from buildwatchcv.infrastructure.minio_client import get_s3_client
from buildwatchcv.settings import get_settings

logger = logging.getLogger(__name__)


def _detect_image_info(data: bytes, object_path: str, fallback_width: int | None, fallback_height: int | None, fallback_format: str | None) -> tuple[int, int, str]:
    """Определить width/height/format. Пытается PIL, иначе fallback из сообщения."""
    # Попытка через Pillow
    try:
        from PIL import Image  # type: ignore

        img = Image.open(io.BytesIO(data))
        w, h = img.size
        fmt = (img.format or "").upper()
        if fmt == "JPG":
            fmt = "JPEG"
        if fmt in ("JPEG", "PNG", "JPG"):
            return w, h, fmt if fmt != "JPG" else "JPEG"
        # неизвестный формат — нормализуем
        if fmt:
            return w, h, fmt
    except ModuleNotFoundError:
        logger.warning("Pillow not installed, using fallback image info")
    except Exception as e:
        logger.warning("PIL detect failed for %s: %s", object_path, e)

    # Fallback — берём из сообщения или эвристика по расширению
    if fallback_width and fallback_height and fallback_format:
        fmt = fallback_format.upper()
        if fmt == "JPG":
            fmt = "JPEG"
        return fallback_width, fallback_height, fmt

    ext = Path(object_path).suffix.lower()
    fmt_map = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG"}
    fmt = fmt_map.get(ext, "JPEG")
    w = fallback_width or 1920
    h = fallback_height or 1080
    return w, h, fmt


async def load_photo(object_path: str, fallback_width: int | None = None, fallback_height: int | None = None, fallback_format: str | None = None) -> tuple[bytes, int, int, str]:
    """Скачать фото из S3 по object_path. Вернуть (bytes, width, height, format)."""
    settings = get_settings()
    s3 = get_s3_client()
    bucket = settings.s3.bucket

    logger.info("downloading photo s3://%s/%s", bucket, object_path)
    data: bytes = await asyncio.to_thread(s3.get_object, bucket, object_path)
    if not data:
        raise ValueError(f"empty object s3://{bucket}/{object_path}")

    w, h, fmt = _detect_image_info(data, object_path, fallback_width, fallback_height, fallback_format)
    logger.info("photo %s: %dx%d %s (%d bytes)", object_path, w, h, fmt, len(data))
    return data, w, h, fmt
