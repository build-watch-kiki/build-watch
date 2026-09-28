import io
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

from minio import Minio

from buildwatchcv.settings import Settings, get_settings

settings = get_settings()


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

    def _ensure_bucket(self, bucket: str) -> None:
        """Создание бакета если отсутствует"""

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
        """Загрузка объекта в S3"""

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
        """Чтение объекта из S3"""

        response = self.client.get_object(bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def remove_object(self, bucket: str, object_name: str) -> None:
        """Удаление объекта из S3"""

        self.client.remove_object(bucket, object_name)

    # Версионирование весов: models/{version}/

    def weights_key(self, version: str, filename: str = "best.pt") -> str:
        """Ключ весов для версии. Версия — произвольное имя: v1, v2-2026-09-24, YOLO-det-v1.2."""
        # get_settings().s3.models_prefix == "models"
        prefix = get_settings().s3.models_prefix.strip("/")
        version = version.strip("/")
        return f"{prefix}/{version}/{filename}"

    def download_to_file(self, bucket: str, object_name: str, dest: Path | str) -> Path:
        """Скачать объект в локальный файл (с созданием директорий)."""
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = self.get_object(bucket, object_name)
        dest.write_bytes(data)
        return dest

    def stat_object(self, bucket: str, object_name: str):
        """Метаданные объекта (Minio stat)."""
        return self.client.stat_object(bucket, object_name)

    def list_objects(self, bucket: str, prefix: str = "", recursive: bool = True) -> list[str]:
        """Список ключей по префиксу."""
        return [o.object_name for o in self.client.list_objects(bucket, prefix=prefix, recursive=recursive)]

    def list_model_versions(self, bucket: str | None = None) -> list[str]:
        """Список доступных версий моделей (папки models/{version}/)."""
        bucket = bucket or get_settings().s3.cv_bucket
        prefix = get_settings().s3.models_prefix.strip("/") + "/"
        keys = self.list_objects(bucket, prefix=prefix)
        versions = sorted({k[len(prefix):].split("/")[0] for k in keys if "/" in k[len(prefix):]})
        return versions


@lru_cache
def get_s3_client():
    return S3Client(get_settings())
