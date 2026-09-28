"""Заливка весов в S3 с версионированием по имени папки.

Каждая версия — отдельная папка: s3://{bucket}/models/{version}/best.pt

Версия — произвольное имя: v1, v2-2026-09-24, YOLO-det-v1.2 и т.д.

Пример:
    venv/Scripts/python.exe scripts/upload_weights.py --version v1 --weights ./best.pt
    venv/Scripts/python.exe scripts/upload_weights.py --version v2-2026-09-24 --weights ./best.pt --config ./config.yaml --copy-latest
"""

import argparse
import logging
from pathlib import Path

from buildwatchcv.infrastructure.minio_client import get_s3_client
from buildwatchcv.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload(version: str, weights: Path, config: Path | None = None, copy_latest: bool = False) -> None:
    if not weights.exists():
        raise FileNotFoundError(f"weights not found: {weights}")

    s3 = get_s3_client()
    settings = get_settings()
    bucket = settings.s3.bucket
    prefix = settings.s3.models_prefix.strip("/")

    version = version.strip().strip("/")
    if not version:
        raise ValueError("version must be non-empty, e.g. v1 or v2-2026-09-24")

    # best.pt
    key = f"{prefix}/{version}/best.pt"
    data = weights.read_bytes()
    s3.put_object(bucket, key, data, content_type="application/octet-stream")
    logger.info("uploaded s3://%s/%s (%d bytes)", bucket, key, len(data))

    # config.yaml опционально
    if config and config.exists():
        cfg_key = f"{prefix}/{version}/config.yaml"
        s3.put_object(bucket, cfg_key, config.read_bytes(), content_type="text/yaml")
        logger.info("uploaded s3://%s/%s", bucket, cfg_key)

    # latest — копия последней версии (опционально)
    if copy_latest:
        latest_key = f"{prefix}/latest/best.pt"
        s3.put_object(bucket, latest_key, data, content_type="application/octet-stream")
        logger.info("copied to s3://%s/%s", bucket, latest_key)

    logger.info("done version=%s -> s3://%s/%s/%s/", version, bucket, prefix, version)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Upload model weights versioned by folder name")
    p.add_argument("--version", required=True, help="Имя версии-папки: v1, v2-2026-09-24, YOLO-det-v1.2")
    p.add_argument("--weights", type=Path, required=True, help="Путь к best.pt")
    p.add_argument("--config", type=Path, default=None, help="Путь к config.yaml (опционально)")
    p.add_argument("--copy-latest", action="store_true", help="Скопировать в models/latest/best.pt")
    args = p.parse_args()
    upload(args.version, args.weights, args.config, args.copy_latest)
