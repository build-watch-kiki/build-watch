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

2. Откройте `deploy/.env` и замените все значения `change_me` своими паролями.

3. Из корня проекта запустите все сервисы одной командой (она одинаковая в
   терминале Linux/macOS и PowerShell):

   ```sh
   docker compose --env-file deploy/.env -f deploy/docker-compose.yaml -f compose.source.yaml --profile full --profile infra up --build -d --wait
   ```

Первый запуск собирает backend, CV и frontend **из файлов этого репозитория**,
поднимает PostgreSQL, RabbitMQ и MinIO, применяет миграции и загружает
справочники. Затем контейнер `model-init` скачивает [веса CV v3](https://github.com/build-watch-kiki/build-watch/releases/tag/model-v3),
проверяет их SHA-256 и помещает в MinIO до старта CV. Повторный запуск сохраняет
данные и уже загруженные веса.

После запуска откройте [интерфейс](http://localhost:3000) или
[документацию API](http://localhost:8000/docs). Для остановки без удаления данных:

```sh
docker compose --env-file deploy/.env -f deploy/docker-compose.yaml -f compose.source.yaml --profile full --profile infra down
```

## Код проекта

| Каталог | Назначение | Версия |
| --- | --- | --- |
| [backend](backend/) | API, хранение данных, обработка результатов CV и расчёт прогресса | `1.0.4` |
| [cv](cv/) | Распознавание техники на фотографиях | `1.0.2` |
| [frontend](frontend/) | Интерфейс объектов, фотографий и аналитики | `1.0.2` |
| [deploy](deploy/) | Базовый Docker Compose, конфигурация и исходная документация | конкурсный снимок |

Четыре каталога содержат зафиксированные файлы исходных проектов как обычный
код, без submodules. [`compose.source.yaml`](compose.source.yaml) переключает
приложения на локальную сборку; сторонние инфраструктурные образы остаются
закреплёнными. [`model-manifest.json`](model-manifest.json) фиксирует адрес и
контрольную сумму весов модели.
