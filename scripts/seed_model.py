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


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("version") != "v2" or manifest.get("object_key") != "models/v2/best.pt":
        raise ValueError("model manifest must target models/v2/best.pt")
    digest = str(manifest.get("sha256", "")).lower()
    if not SHA256_PATTERN.fullmatch(digest):
        raise ValueError("model manifest must contain a 64-character SHA-256")
    manifest["sha256"] = digest
    return manifest


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


def main() -> None:
    manifest = load_manifest()
    client = minio_client("S3__")
    bucket = os.environ["S3__CV_BUCKET"]
    key = manifest["object_key"]

    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    if is_seeded(client, bucket, key, manifest["sha256"]):
        print(f"[model-init] {bucket}/{key} already matches {manifest['sha256']}")
        return

    source = minio_client("MODEL_SOURCE_")
    source_bucket = os.environ["MODEL_SOURCE_BUCKET"]
    source_object = source.get_object(source_bucket, key)
    digest = hashlib.sha256()
    size = 0
    try:
        with tempfile.TemporaryFile() as model_file:
            while chunk := source_object.read(CHUNK_SIZE):
                model_file.write(chunk)
                digest.update(chunk)
                size += len(chunk)
            if digest.hexdigest() != manifest["sha256"]:
                raise ValueError("source S3 model checksum mismatch")
            model_file.seek(0)
            client.put_object(
                bucket,
                key,
                model_file,
                length=size,
                content_type="application/octet-stream",
                metadata={"sha256": manifest["sha256"]},
            )
    finally:
        source_object.close()
        source_object.release_conn()
    print(f"[model-init] copied {source_bucket}/{key} to {bucket}/{key} ({size} bytes)")


if __name__ == "__main__":
    main()
