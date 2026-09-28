# Build Watch Backend

Бэкенд-сервис на FastAPI / FastStream

## Требования

- Python 3.14
- [uv](https://github.com/astral-sh/uv) (рекомендуется) или стандартный `pip`
- Настроенный файл `.env`

---

## Запуск приложения

### Вариант 1: Через `uv`

1. Установите зависимости:
   ```bash
   uv sync --locked
   ```
2. Запустите приложение:
   ```bash
   uv run python -m buildwatch.main
   ```

### Вариант 2: Через стандартный `requirements.txt` и `pip`

Приложение полностью готово к запуску через классический `requirements.txt`:

1. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   # Linux / WSL:
   source .venv/bin/activate
   # Windows:
   .venv\Scripts\activate
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Запустите приложение:
   ```bash
   python -m buildwatch.main
   ```

### Вариант 3: Через Docker Compose  (Рекомендуемый)

```bash
docker compose --profile infra up --build
```

Compose запускает `app` для HTTP и публикации `new-photo`, а `worker` отдельно обрабатывает `cv-result`. Миграции выполняет только `app` перед запуском; `worker` ждёт его готовности. После успешного ответа CV API возвращает исходный URL фото и координаты `detections` для наложения на клиенте; серверный preview не создаётся.

---

## Проверка работоспособности

После запуска приложения (по умолчанию `http://localhost:8080`) доступны следующие healthcheck-эндпоинты:

- **Общая проверка приложения:**  
  `GET /health` → `{"message": "ok"}`
- **Проверка подключения к PostgreSQL:**  
  `GET /health/db`
- **Проверка подключения к S3 / MinIO:**  
  `GET /health/s3`
- **Проверка подключения к RabbitMQ:**  
  `GET /health/broker`

Интерактивная документация Swagger UI доступна по адресу:  
`http://localhost:8080/docs`

## Суточный анализ план-факт

После каждого успешного CV-ответа worker пересчитывает календарный день проекта:
повторные снимки одного объекта не суммируются, а количество каждого вида техники
определяется по 75-му перцентилю независимых наблюдений. Компактная история и
детали выбранного дня доступны раздельно:

```http
GET /projects/{project_id}/progress/daily?from=2026-09-01&to=2026-09-25
GET /projects/{project_id}/progress/daily/2026-09-25
```

`GET /projects/{project_id}/stages/gantt` возвращает плановые этапы вместе с
необязательным объектом `actual`: фактическим интервалом, статусом, отклонением
в днях, числом отклонений по технике и готовым русским сообщением. Изменение
этапов или их техники пересчитывает уже материализованную аналитику проекта.

Для фотографий, обработанных до установки этой версии, выполните идемпотентный
backfill после миграций:

```bash
uv run python -m buildwatch.progress.recalculate
uv run python -m buildwatch.progress.recalculate --project-id 1
```

Пороги задаются переменными `ANALYSIS__TIMEZONE`,
`ANALYSIS__MIN_CONFIDENCE`, `ANALYSIS__MINIMUM_STAGE_SCORE` и
`ANALYSIS__TRANSITION_MARGIN`.
