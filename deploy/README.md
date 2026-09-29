# Build Watch

Build Watch - интеллектуальная система мониторинга строительной площадки для кейса № 7 хакатона «Лидеры цифровой трансформации 2026». Она принимает фотографии стройки, распознаёт технику, сопоставляет наблюдения с календарным планом и показывает руководителю фактический прогресс и отклонения.

Этот каталог содержит Docker Compose и настройки сервисов. Исходники приложений находятся в соседних каталогах `backend`, `cv` и `frontend`.

## Материалы

- [Описание решения](../docs/solution.md)
- [Архитектура и поток данных](../docs/architecture.md)
- [Презентация](../docs/presentation.pdf)

## Запуск

Запуск из исходников описан в [корневом README](../README.md#запуск). Образы инфраструктуры закреплены по digest SHA-256.

Потребуются Docker Engine и Docker Compose v2.
В `deploy/.env` задайте `MODEL_SOURCE_*` для S3 с весами v2, v3 и v4.

```bash
cd build-watch
cp deploy/.env.example deploy/.env
docker compose --env-file deploy/.env -f deploy/docker-compose.yaml -f compose.source.yaml --profile full --profile infra up --build -d --wait
```

При первом запуске одноразовый контейнер `build-watch-init` автоматически:

1. применяет миграции и загружает полный справочник доступной техники;
2. загружает типы объектов и доступные этапы работ командой `python -m buildwatch.utils.seed`;
3. только после успешной инициализации запускает API и worker.

Инициализация идемпотентна: команду можно безопасно выполнить повторно с уже существующими данными.

После запуска доступны:

- интерфейс: <http://localhost:3000>;
- Swagger API: <http://localhost:8000/docs>;
- RabbitMQ Management: <http://localhost:15672>;
- MinIO Console: <http://localhost:9001>.

Проверка состояния и остановка:

```bash
docker compose --env-file deploy/.env \
  -f deploy/docker-compose.yaml -f compose.source.yaml \
  --profile full --profile infra ps

docker compose --env-file deploy/.env \
  -f deploy/docker-compose.yaml -f compose.source.yaml \
  --profile full --profile infra down
```

## Режимы образов

Без `compose.source.yaml` базовый Compose использует образы из GHCR. Их версии задают `BACKEND_VERSION`, `CV_VERSION` и `FRONTEND_VERSION` в `deploy/.env`:

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yaml --profile full --profile infra up -d
```

При запуске с `compose.source.yaml` приложения собираются из локального кода.

MinIO использует именованный volume `miniodata`: на чистом запуске он пустой, а фотографии сохраняются при пересоздании контейнера. Удаляйте volume через `down -v`, если нужен полный сброс.

## Обновление development-сборки

Push в основные ветки компонентных репозиториев публикует два Docker-тега:

- `latest` — текущая development-сборка;
- `sha-<commit>` — сборка конкретного коммита.

Git-тег формата `X.Y.Z` публикует одноимённый Docker-тег, не перемещая `latest`.

Сохранённый в `deploy/.github` workflow `Server Deploy` использует базовый `docker-compose.yaml` и версии из секрета `ENV_FILE`. В монорепозитории GitHub Actions не запускает workflow из вложенного каталога.

## Сервисы

| Сервис                       | Назначение                                   | Профиль                                 |
|------------------------------|----------------------------------------------|-----------------------------------------|
| `build-watch-init`           | Миграции и начальное заполнение справочников | всегда, завершается после инициализации |
| `build-watch-frontend`       | Пользовательский интерфейс и аналитика       | `full`, `frontend`                      |
| `build-watch-backend`        | REST API и бизнес-логика                     | всегда                                  |
| `build-watch-backend-worker` | Приём результатов CV и обновление прогресса  | всегда                                  |
| `build-watch-cv`             | Детекция и подсчёт строительной техники      | `full`, `cv`                            |
| `postgres`                   | Данные проектов, планов и аналитики          | `infra`                                 |
| `rabbitmq`                   | Очереди обработки фотографий                 | `infra`                                 |
| `minio`                      | S3-совместимое хранилище фотографий          | `infra`                                 |

## Безопасность

Секреты не хранятся в Git. Коммитится только `.env.example`; рабочий `.env` исключён через `.gitignore`. Для публичного развёртывания обязательно замените демонстрационные пароли.
