# Build Watch

**Интеллектуальный мониторинг строительной площадки** для кейса № 7 хакатона
«Лидеры цифровой трансформации 2026». Build Watch распознаёт строительную
технику на фотографиях, сопоставляет наблюдения с календарным планом и показывает
фактический прогресс и отклонения.

## Материалы

- [Описание решения](docs/solution.md) — задача, подход и демонстрационный сценарий.
- [Архитектура](docs/architecture.md) — компоненты и поток обработки фотографии.
- [Презентация в PDF](docs/presentation.pdf) и [исходник PowerPoint](docs/presentation.pptx).

## Запуск

Потребуются Docker Engine, Docker Compose v2 и интернет для первоначальной
сборки и загрузки весов модели. Все исходники приложений находятся в этом
репозитории; доступ к другим репозиториям не требуется.

1. Клонируйте проект и создайте файл настроек:

   ```sh
   git clone https://github.com/build-watch-kiki/build-watch.git
   cd build-watch
   cp deploy/.env.example deploy/.env
   ```

   В PowerShell последняя команда — `Copy-Item deploy/.env.example deploy/.env`.

2. Откройте `deploy/.env`, замените все значения `change_me` своими паролями и
   укажите доступ к исходному S3 в полях `MODEL_SOURCE_*`.

3. Из корня проекта запустите все сервисы одной командой (она одинаковая в
   терминале Linux/macOS и PowerShell):

   ```sh
   docker compose --env-file deploy/.env -f deploy/docker-compose.yaml -f compose.source.yaml --profile full --profile infra up --build -d --wait
   ```

Первый запуск собирает backend, CV и frontend **из файлов этого репозитория**,
поднимает PostgreSQL, RabbitMQ и MinIO, применяет миграции и загружает
справочники. Затем контейнер `model-init` копирует веса CV v2, v3 и v4 из
указанного S3, проверяет их SHA-256 и помещает в MinIO до старта CV. Повторный запуск сохраняет
данные и уже загруженные веса.

Активную модель выбирает `S3__MODEL_VERSION` в `deploy/.env` (`v2`, `v3` или `v4`).
После смены значения пересоздайте CV-контейнер:

```sh
docker compose --env-file deploy/.env -f deploy/docker-compose.yaml -f compose.source.yaml --profile full --profile infra up -d --no-build --no-deps --force-recreate build-watch-cv
```

После запуска откройте [интерфейс](http://localhost:3000) или
[документацию API](http://localhost:8000/docs). Для остановки без удаления данных:

```sh
docker compose --env-file deploy/.env -f deploy/docker-compose.yaml -f compose.source.yaml --profile full --profile infra down
```

## Код проекта

| Каталог | Назначение | Версия |
| --- | --- | --- |
| [backend](backend/) | API, хранение данных, обработка результатов CV и расчёт прогресса | `1.0.7` |
| [cv](cv/) | Распознавание техники на фотографиях | `1.0.2` |
| [frontend](frontend/) | Интерфейс объектов, фотографий и аналитики | `1.0.6` |
| [deploy](deploy/) | Базовый Docker Compose и конфигурация сервисов | текущая конфигурация |

Четыре каталога содержат зафиксированные файлы исходных проектов как обычный
код, без submodules. [`compose.source.yaml`](compose.source.yaml) переключает
приложения на локальную сборку; сторонние инфраструктурные образы остаются
закреплёнными. [`model-manifest.json`](model-manifest.json) фиксирует ключ и
контрольную сумму весов модели.
