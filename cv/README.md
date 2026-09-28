# build-watch-cv

CV-воркер для `build-watch` — получает и подтверждает события о новых фото из RabbitMQ. Стек: Python 3.14 + FastStream (Rabbit) + Minio.

## Быстрый старт

```bash
cp .env.example .env   # поправь BROKER__HOST / S3__ENDPOINT если нужно
uv run faststream run buildwatchcv.main:app
```

Docker (воркер, без HTTP):

```bash
docker compose -f docker-compose.yaml -f docker-compose.local.yaml \
  --profile local-infra up --build
```

Для подключения к уже запущенной сети `build-watch-deploy_default` используйте
`docker compose -f docker-compose.yaml -f docker-compose.deploy.yaml up --build`
и задайте в `.env` адреса `BROKER__HOST` и `S3__ENDPOINT`, доступные контейнеру.
Без дополнительного файла Compose использует адреса из `.env` и собственную сеть.

## Конфигурация

`buildwatchcv/settings.py` (`pydantic-settings`, `env_nested_delimiter="__"`). Загружает `.env.example` затем `.env` — второй переопределяет первый.

| Переменная | Дефолт | Описание |
|---|---|---|
| `BROKER__HOST/PORT/USERNAME/PASSWORD` | `localhost:5672 / guest` | RabbitMQ, собирается в `RABBITMQ_DSN` |
| `BROKER__QUEUE__NEW_PHOTOS` | `new-photo` | Очередь новых фото (`BrokerQueues`) |
| `BROKER__QUEUE__CV_RESULT` | `cv-result` | Очередь результатов CV |
| `S3__ENDPOINT` | `http://localhost:9000` | MinIO/S3 эндпоинт |
| `S3__ACCESS_KEY/SECRET_KEY/BUCKET` | `minioadmin / app-bucket` | Креды и бакет |
| `S3__MODELS_PREFIX` | `models` | Папка версий весов |
| `OUTPUT__ENABLED` | `false` | Локальный debug-дамп фото и детекций |

Docker-образ использует CPU-сборки PyTorch. При недоступных весах или ошибке
инференса воркер публикует `failed`; фиктивные детекции не создаются.
`S3Client` — синхронный клиент MinIO.
