"""TEMP-DEBUG: локальный дамп результата пер-фото в папку.

Временная мера, на проде не будет — удалить вместе с annotate.py
и шагом 4 в pipeline.py.

Структура: {out_root}/{version}/{object_path...}/
    original.<ext>   исходные байты из S3
    annotated.jpg    фото с наложенными bbox
    response.json    DetectionResponse целиком
"""

import logging
from pathlib import Path

from buildwatchcv.schemas.response import DetectionResponse

logger = logging.getLogger(__name__)


def _safe_subpath(object_path: str) -> Path:
    """object_path -> относительный путь без .. и якорей."""
    parts = [
        p
        for p in Path(object_path).parts
        if p not in ("", ".", "..", "/", "\\") and ".." not in p
    ]
    if not parts:
        raise ValueError(f"bad object_path: {object_path!r}")
    return Path(*parts)


def save_debug_run(
    out_root: Path | str,
    version: str,
    object_path: str,
    original_bytes: bytes,
    annotated_bytes: bytes,
    response: DetectionResponse,
) -> Path:
    """Сохранить original + annotated + response.json. Вернуть папку."""
    version = version.strip().strip("/") or "unknown"
    folder = Path(out_root) / version / _safe_subpath(object_path)
    folder.mkdir(parents=True, exist_ok=True)

    ext = Path(object_path).suffix.lower() or ".jpg"
    (folder / f"original{ext}").write_bytes(original_bytes)
    (folder / "annotated.jpg").write_bytes(annotated_bytes)
    (folder / "response.json").write_text(
        response.model_dump_json(indent=2), encoding="utf-8"
    )
    logger.info("debug dump -> %s", folder)
    return folder
