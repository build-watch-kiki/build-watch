"""Seed the pinned CV weights into MinIO before starting the CV worker."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from minio import Minio
from minio.error import S3Error

MANIFEST_PATH = Path("/scripts/model-manifest.json")
CHUNK_SIZE = 8 * 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


def valid_sha256(value: str) -> str:
    value = value.lower()
    if not SHA256_PATTERN.fullmatch(value):
        raise ValueError("model manifest must contain a 64-character SHA-256")
    return value


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["sha256"] = valid_sha256(manifest["sha256"])
    if not manifest.get("assets"):
        raise ValueError("model manifest has no release assets")
    for asset in manifest["assets"]:
        asset["sha256"] = valid_sha256(asset["sha256"])
        if not asset["url"].startswith("https://github.com/build-watch-kiki/build-watch/releases/download/model-v3/"):
            raise ValueError("model asset URL must point to the pinned model-v3 release")
    if manifest["object_key"] != "models/v3/best.pt":
        raise ValueError("model manifest must target models/v3/best.pt")
    return manifest


def get_minio_client() -> Minio:
    endpoint = urlsplit(os.environ["S3__ENDPOINT"])
    if endpoint.scheme not in ("http", "https") or not endpoint.netloc:
        raise ValueError("S3__ENDPOINT must be an HTTP or HTTPS URL")
    return Minio(
        endpoint.netloc,
        access_key=os.environ["S3__ACCESS_KEY"],
        secret_key=os.environ["S3__SECRET_KEY"],
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


def download_assets(manifest: dict, destination) -> int:
    full_digest = hashlib.sha256()
    total_size = 0
    for asset in manifest["assets"]:
        part_digest = hashlib.sha256()
        request = Request(asset["url"], headers={"User-Agent": "build-watch-model-init"})
        with urlopen(request, timeout=60) as response:
            while chunk := response.read(CHUNK_SIZE):
                destination.write(chunk)
                part_digest.update(chunk)
                full_digest.update(chunk)
                total_size += len(chunk)
        if part_digest.hexdigest() != asset["sha256"]:
            raise ValueError(f"model release asset checksum mismatch: {asset['url']}")
    if full_digest.hexdigest() != manifest["sha256"]:
        raise ValueError("reassembled model checksum mismatch")
    return total_size


def main() -> None:
    manifest = load_manifest()
    client = get_minio_client()
    bucket = os.environ["S3__CV_BUCKET"]
    key = manifest["object_key"]

    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    if is_seeded(client, bucket, key, manifest["sha256"]):
        print(f"[model-init] {bucket}/{key} already matches {manifest['sha256']}")
        return

    with tempfile.TemporaryFile() as model_file:
        size = download_assets(manifest, model_file)
        model_file.seek(0)
        client.put_object(
            bucket,
            key,
            model_file,
            length=size,
            content_type="application/octet-stream",
            metadata={"sha256": manifest["sha256"]},
        )
    print(f"[model-init] seeded {bucket}/{key} ({size} bytes)")


if __name__ == "__main__":
    main()
