# Build Watch

Build Watch - интеллектуальная система мониторинга строительной площадки для кейса № 7 хакатона «Лидеры цифровой трансформации 2026». Она принимает фотографии стройки, распознаёт технику, сопоставляет наблюдения с календарным планом и показывает руководителю фактический прогресс и отклонения.

Этот репозиторий - точка входа для запуска проекта: здесь находятся Docker Compose для всех сервисов, инструкция для воспроизведения конкурсной версии, а также описание решения и архитектуры.

## Материалы

- [Описание решения](docs/solution.md)
- [Архитектура и поток данных](docs/architecture.md)
- [Презентация](docs/presentation.pdf)

## Запуск

Этот способ запускает конкурсную версию: образы приложений указаны по версиям, а образы инфраструктуры закреплены по digest SHA-256.

Потребуются Docker Engine и Docker Compose v2.

```bash
git clone https://github.com/build-watch-kiki/build-watch-deploy.git
cd build-watch-deploy
cp .env.example .env
docker compose -f docker-compose.yaml -f docker-compose.submission.yaml --profile full --profile infra up -d --wait
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
docker compose \
  -f docker-compose.yaml \
  -f docker-compose.submission.yaml \
  --profile full --profile infra ps

docker compose \
  -f docker-compose.yaml \
  -f docker-compose.submission.yaml \
  --profile full --profile infra down
```

## Development-запуск

Потребуются Docker Engine и Docker Compose v2.

```bash
git clone https://github.com/build-watch-kiki/build-watch-deploy.git
cd build-watch-deploy
cp .env.example .env
docker compose --profile full --profile infra up -d
```

Пароли и порты задаются в `.env`. Для локального запуска замените значения `change_me` в созданном файле.

Проверка состояния и остановка:

```bash
docker compose --profile full --profile infra ps
docker compose --profile full --profile infra down
```

## Режимы образов

Обычный compose сохраняет совместимость с процессом разработки. Переменная `VERSION` по умолчанию равна `latest`, поэтому новые сборки можно запускать без изменения конфигурации:

```bash
docker compose --profile full up -d
VERSION=sha-abcdef0 docker compose --profile full up -d
```

Для воспроизведения отправленной на хакатон версии используйте запуск для жюри в самом начале документа. `docker-compose.submission.yaml` не содержит плавающих тегов.

MinIO использует именованный volume `miniodata`: на чистом запуске он пустой, а фотографии сохраняются при пересоздании контейнера. Удаляйте volume через `down -v`, если нужен полный сброс.

## Обновление development-сборки

Push в основные ветки компонентных репозиториев публикует два Docker-тега:

- `latest` — текущая development-сборка;
- `sha-<commit>` — сборка конкретного коммита.

Git-тег формата `X.Y.Z` публикует одноимённый Docker-тег, не перемещая `latest`.

Dev CI/CD использует только базовый `docker-compose.yaml` и автоматически разворачивает `latest` после push компонентных репозиториев. Ручной запуск workflow `Server Deploy` делает то же самое. Submission override не участвует в CI/CD и используется только в команде запуска для жюри в начале README.

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
