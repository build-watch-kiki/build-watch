"""Copy pinned CV weights from source S3 into MinIO before starting CV."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from minio import Minio
from minio.error import S3Error

MANIFEST_PATH = Path("/scripts/model-manifest.json")
CHUNK_SIZE = 8 * 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def load_manifest() -> list[dict]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    models = manifest.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError("model manifest must contain models")
    versions = set()
    for model in models:
        version = model.get("version")
        if not isinstance(version, str) or not re.fullmatch(r"v[0-9]+", version):
            raise ValueError("model version must look like v2")
        if version in versions:
            raise ValueError(f"duplicate model version: {version}")
        versions.add(version)
        if model.get("object_key") != f"models/{version}/best.pt":
            raise ValueError(f"invalid target key for {version}")
        source_key = model.get("source_key")
        if not isinstance(source_key, str) or not source_key.startswith(f"models/{version}/"):
            raise ValueError(f"invalid source key for {version}")
        digest = str(model.get("sha256", "")).lower()
        if not SHA256_PATTERN.fullmatch(digest):
            raise ValueError(f"invalid SHA-256 for {version}")
        model["sha256"] = digest
    return models


def minio_client(prefix: str) -> Minio:
    endpoint = urlsplit(os.environ[f"{prefix}ENDPOINT"])
    if endpoint.scheme not in ("http", "https") or not endpoint.netloc:
        raise ValueError(f"{prefix}ENDPOINT must be an HTTP or HTTPS URL")
    return Minio(
        endpoint.netloc,
        access_key=os.environ[f"{prefix}ACCESS_KEY"],
        secret_key=os.environ[f"{prefix}SECRET_KEY"],
        secure=endpoint.scheme == "https",
    )


def is_seeded(client: Minio, bucket: str, key: str, sha256: str) -> bool:
    try:
        stat = client.stat_object(bucket, key)
    except S3Error as exc:
        if exc.code in ("NoSuchKey", "NoSuchBucket", "NoSuchObject"):
            return False
        raise
    metadata = {name.lower(): value for name, value in stat.metadata.items()}
    return metadata.get("x-amz-meta-sha256") == sha256


def copy_model(
    source: Minio, source_bucket: str, target: Minio, target_bucket: str, model: dict
) -> None:
    source_key = model["source_key"]
    target_key = model["object_key"]
    expected_digest = model["sha256"]
    source_object = source.get_object(source_bucket, source_key)
    digest = hashlib.sha256()
    size = 0
    try:
        with tempfile.TemporaryFile() as model_file:
            while chunk := source_object.read(CHUNK_SIZE):
                model_file.write(chunk)
                digest.update(chunk)
                size += len(chunk)
            if digest.hexdigest() != expected_digest:
                raise ValueError(f"source S3 model checksum mismatch: {source_key}")
            model_file.seek(0)
            target.put_object(
                target_bucket,
                target_key,
                model_file,
                length=size,
                content_type="application/octet-stream",
                metadata={"sha256": expected_digest},
            )
    finally:
        source_object.close()
        source_object.release_conn()
    print(
        f"[model-init] copied {source_bucket}/{source_key} "
        f"to {target_bucket}/{target_key} ({size} bytes)"
    )


def main() -> None:
    models = load_manifest()
    target = minio_client("S3__")
    target_bucket = os.environ["S3__CV_BUCKET"]
    if not target.bucket_exists(target_bucket):
        target.make_bucket(target_bucket)

    source = None
    source_bucket = None
    for model in models:
        key = model["object_key"]
        if is_seeded(target, target_bucket, key, model["sha256"]):
            print(f"[model-init] {target_bucket}/{key} already matches {model['sha256']}")
            continue
        if source is None:
            source = minio_client("MODEL_SOURCE_")
            source_bucket = os.environ["MODEL_SOURCE_BUCKET"]
        copy_model(source, source_bucket, target, target_bucket, model)


if __name__ == "__main__":
    main()
