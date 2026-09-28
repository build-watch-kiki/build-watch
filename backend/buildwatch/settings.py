from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class LogSettings(BaseModel):
    """Настройки логирования"""

    level: str = "INFO"


class AppSettings(BaseModel):
    """Настройки приложения"""

    title: str = "Build Watch API"
    debug: bool = False


class RunSettings(BaseModel):
    """Параметры запуска HTTP-сервера"""

    port: int = 8000
    host: str = "localhost"
    prefix: str = "/api/v1"


class FileSettings(BaseModel):
    """Пути к файлам и директориям проекта"""

    base_dir: Path = Path(__file__).resolve().parent.parent
    src_dir: Path = base_dir / "buildwatch"

    env_file: Path = base_dir / ".env"
    env_example_file: Path = base_dir / ".env.example"


class DatabaseSettings(BaseModel):
    """Настройки подключения к PostgreSQL"""

    host: str = "postgres"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    name: str = "build-watch-db"

    @property
    def POSTGRES_DSN(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class S3Settings(BaseModel):
    """Настройки S3-совместимого хранилища"""

    endpoint: str = "http://localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    bucket: str = "buildwatch"


class BrokerQueues(BaseModel):
    new_photo: str = "new-photo"
    cv_result: str = "cv-result"


class BrokerSettings(BaseModel):
    """Настройки брокера сообщений RabbitMQ"""

    host: str = "localhost"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    queue: BrokerQueues = BrokerQueues()

    @property
    def RABBITMQ_DSN(self) -> str:
        return f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/"


class UseMocksSettings(BaseModel):
    """Переключатели моков для разработки"""

    stage_repo: bool = False
    technique_repo: bool = False


class AnalysisSettings(BaseModel):
    """Пороговые значения суточного анализа план-факт."""

    timezone: str = "Europe/Moscow"
    min_confidence: float = 0.50
    minimum_stage_score: float = 0.60
    transition_margin: float = 0.10


class Settings(BaseSettings):
    """Корневая конфигурация приложения"""

    app: AppSettings = AppSettings()
    files: FileSettings = FileSettings()
    run: RunSettings = RunSettings()
    db: DatabaseSettings = DatabaseSettings()
    s3: S3Settings = S3Settings()
    broker: BrokerSettings = BrokerSettings()
    log: LogSettings = LogSettings()
    use_mock: UseMocksSettings = UseMocksSettings()
    analysis: AnalysisSettings = AnalysisSettings()

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env.example", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings():
    return Settings()  # type: ignore
