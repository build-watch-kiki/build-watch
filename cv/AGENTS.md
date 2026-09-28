# AGENTS.md — build-watch-cv

## Стек и окружение
- Python `>=3.14` (зафиксирован в `.python-version`, `pyproject.toml`, `Dockerfile` — `ghcr.io/astral-sh/uv:python3.14-bookworm-slim`).
- Менеджер — строго `uv` в Linux/WSL. Запрещены `pip install`, `uv pip install`, `uv sync`, `uv add`, создание `.venv` на `/mnt/c` (см. глобальный `AGENTS.md`). Команды: `uv run <command>`, разовые проверки `uv run --with <pkg>`, утилиты `uvx <tool>`.
- Текущий `.venv` указывает на Windows-путь (`C:\Users\...`) — не трогать, не пересоздавать.

## Структура
- Пакет — `buildwatchcv/` (не `buildwatch`). Точка входа `buildwatchcv/main.py` сейчас пустая — заглушка.
- `buildwatchcv/settings.py` — единственный источник конфигурации (`pydantic-settings`). `buildwatchcv/infrastructure/broker.py` — `FastStream RabbitBroker`, `buildwatchcv/infrastructure/minio_client.py` — синхронный `Minio` клиент (`S3Client`).
- Связанные репозитории рядом: `build-watch-backend` (пакет `buildwatch`), `build-watch-deploy` — не трогать без запроса.

## Конфигурация (settings.py:41)
- `Settings` грузит `env_file=(BASE_DIR / ".env.example", BASE_DIR / ".env")` — второй файл переопределяет первый. `env_nested_delimiter="__"`, `extra="ignore"`.
- `BASE_DIR = Path(__file__).resolve().parent.parent` (корень репо).
- Переменные: `RUN__PORT`, `BROKER__HOST/PORT/USERNAME/PASSWORD`, `BROKER__QUEUE__NEW_PHOTOS` (по умолчанию `new-photos`), `S3__ENDPOINT/ACCESS_KEY/SECRET_KEY/BUCKET` — см. `.env.example:1`.
- `FileSettings.src_dir` сейчас указывает на `base_dir / "buildwatch"` (settings.py:12) — баг, должен быть `buildwatchcv`.

## Docker — известные баги, чинить перед сборкой
- `Dockerfile:9` `COPY buildwatch ./buildwatch` и `Dockerfile:15` `CMD ["uvicorn", "buildwatch.main:app"...]` — оба указывают на несуществующий пакет `buildwatch`, должно быть `buildwatchcv`. Иначе `docker compose build` падает.
- `docker-compose.yaml:11` корректно монтирует `./buildwatchcv:/app/buildwatchcv`, сервис `cv-worker`, порт `${RUN__PORT}:8000`.

## Команды
- Установка (только чтение окружения, не писать в `.venv`): `uv sync --locked` запрещён глобальными правилами — для проверки используй `uv run --with <pkg> <cmd>`.
- Локальный запуск воркера (после реализации `main.py`): `uv run python -m buildwatchcv.main` или `uv run faststream run buildwatchcv.infrastructure.broker:broker`.
- Docker: `docker compose up --build` (требует `.env` рядом с `docker-compose.yaml`).

## Что отсутствует
- Нет тестов, линтеров, форматтеров, CI, `opencode.json`, `Makefile` — не выдумывать команды.
- `README.md` пустой, `requirements.txt` — артефакт `uv pip compile`, источник правды — `pyproject.toml` + `uv.lock`.
