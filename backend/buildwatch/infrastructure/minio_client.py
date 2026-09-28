import io
from collections import OrderedDict
from datetime import timedelta
from functools import lru_cache
from threading import Lock
from time import monotonic
from typing import Annotated, BinaryIO

from fastapi import Depends
from minio import Minio

from buildwatch.settings import Settings, get_settings

settings = get_settings()
PRESIGNED_URL_EXPIRES = timedelta(days=1)
PRESIGNED_URL_REFRESH_BUFFER = timedelta(minutes=1)
PRESIGNED_URL_CACHE_SIZE = 10_000
BROWSER_CACHE_CONTROL = "private, max-age=86400"


class S3Client:
    """Обычный синхронный клиент Minio/S3"""

    def __init__(self, s3_settings: Settings):
        endpoint = (
            s3_settings.s3.endpoint.replace("http://", "")
            .replace("https://", "")
            .rstrip("/")
        )
        secure = s3_settings.s3.endpoint.startswith("https://")
        self.client = Minio(
            endpoint=endpoint,
            access_key=s3_settings.s3.access_key,
            secret_key=s3_settings.s3.secret_key,
            secure=secure,
        )
        self._presigned_url_cache: OrderedDict[
            tuple[str, str, int], tuple[str, float]
        ] = OrderedDict()
        self._presigned_url_cache_lock = Lock()

    def _ensure_bucket(self, bucket: str) -> None:
        """Гарантирует существование бакета"""

        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def put_object(
        self,
        bucket: str,
        object_name: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        length: int | None = None,
    ) -> str:
        """Загрузка объекта в бакет"""

        self._ensure_bucket(bucket)
        if isinstance(data, bytes):
            length = len(data)
            data = io.BytesIO(data)

        if length is None:
            raise ValueError("length обязателен")

        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=data,
            length=length,
            content_type=content_type,
        )
        return object_name

    def get_object(self, bucket: str, object_name: str) -> bytes:
        """Чтение объекта из бакета"""

        response = self.client.get_object(bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def remove_object(self, bucket: str, object_name: str) -> None:
        """Удаление объекта из бакета"""

        self.client.remove_object(bucket, object_name)

    def get_presigned_url(
        self,
        bucket: str,
        object_name: str,
        expires_minutes: int = int(PRESIGNED_URL_EXPIRES.total_seconds() // 60),
    ) -> str:
        """Возвращает переиспользуемую временную ссылку для фронта.

        Одинаковый URL позволяет браузеру применить собственный HTTP-кеш. Ссылка
        обновляется немного заранее, чтобы не вернуть клиенту почти истёкший URL.
        """

        cache_key = (bucket, object_name, expires_minutes)
        now = monotonic()
        with self._presigned_url_cache_lock:
            cached = self._presigned_url_cache.get(cache_key)
            if cached is not None and cached[1] > now:
                self._presigned_url_cache.move_to_end(cache_key)
                return cached[0]

            expires = timedelta(minutes=expires_minutes)
            url = self.client.presigned_get_object(
                bucket,
                object_name,
                expires=expires,
                response_headers={"response-cache-control": BROWSER_CACHE_CONTROL},
            )
            refresh_after = now + max(
                0, (expires - PRESIGNED_URL_REFRESH_BUFFER).total_seconds()
            )
            self._presigned_url_cache[cache_key] = (url, refresh_after)
            self._presigned_url_cache.move_to_end(cache_key)
            if len(self._presigned_url_cache) > PRESIGNED_URL_CACHE_SIZE:
                self._presigned_url_cache.popitem(last=False)
            return url


@lru_cache(maxsize=1)
def get_s3_client() -> S3Client:
    return S3Client(s3_settings=settings)


S3ClientDep = Annotated[S3Client, Depends(get_s3_client)]
