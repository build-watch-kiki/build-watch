from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class FileSettings(BaseModel):
    """Пути проекта и env-файлов"""

    base_dir: Path = Path(__file__).resolve().parent.parent
    src_dir: Path = base_dir / "buildwatchcv"

    env_file: Path = base_dir / ".env"
    env_example_file: Path = base_dir / ".env.example"


class S3Settings(BaseModel):
    """Настройки S3/MinIO"""

    endpoint: str = "http://localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    bucket: str = "buildwatch"
    cv_bucket: str = "buildwatch-cv"
    models_prefix: str = "models"
    model_name: str = "constr_yolo"
    model_version: str = "v3"


class BrokerQueues(BaseModel):
    """Имена очередей брокера"""

    new_photos: str = "new-photo"
    cv_result: str = "cv-result"


class OutputSettings(BaseModel):
    """TEMP-DEBUG: локальный дамп результатов. Удалить перед продом."""

    enabled: bool = False
    dir: Path = Path("../_cv_debug")

    @property
    def resolved_dir(self) -> Path:
        d = self.dir
        if not d.is_absolute():
            d = BASE_DIR / d
        return d


class BrokerSettings(BaseModel):
    """Настройки подключения к RabbitMQ"""

    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    queue: BrokerQueues = BrokerQueues()

    @property
    def RABBITMQ_DSN(self) -> str:
        return f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/"


class Settings(BaseSettings):
    files: FileSettings = FileSettings()
    s3: S3Settings = S3Settings()
    broker: BrokerSettings = BrokerSettings()
    output: OutputSettings = OutputSettings()

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env.example", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings():
    return Settings()  # type: ignore
