# Build Watch — исходники конкурсной версии

Этот репозиторий содержит читаемый код всех четырёх частей Build Watch. Один клон
достаточен для просмотра кода и сборки приложений из исходников. Для запуска
нужны Docker Engine, Docker Compose v2 и доступ в интернет для базовых образов,
зависимостей и файла весов модели.

| Каталог | Исходный репозиторий | Зафиксированная версия | Git commit |
| --- | --- | --- | --- |
| [`backend/`](backend/) | `build-watch-backend` | `1.0.4` | `77135d1677e3019520a5b0913dd46c64f8f09e5f` |
| [`cv/`](cv/) | `build-watch-cv` | `1.0.2` | `e90e63781894ca1a55591cb34de539c3364d77ab` |
| [`frontend/`](frontend/) | `build-watch-frontend` | `1.0.2` | `46f219bc9ef2399f3438f56c18af998e996c17ea` |
| [`deploy/`](deploy/) | `build-watch-deploy` | снимок Compose | `99afbfc216ba9865ee7a6fbbb217b1bd3cf2e9f2` |

Каталоги импортированы из Git-коммитов без локальных изменений и вложенных
`.git`. Доступ к исходным четырём репозиториям для просмотра и запуска не нужен:
их зафиксированные файлы полностью находятся здесь. Документация в `deploy/`
описывает исходный репозиторий с образами;
для воспроизводимого запуска **из кода этого репозитория** используйте команду ниже.

## Запуск из исходников

Создайте `deploy/.env` из [`deploy/.env.example`](deploy/.env.example) и замените
значения `change_me`. В Linux/macOS:

```sh
git clone https://github.com/build-watch-kiki/build-watch.git
cd build-watch
cp deploy/.env.example deploy/.env
docker compose --env-file deploy/.env \
  -f deploy/docker-compose.yaml -f compose.source.yaml \
  --profile full --profile infra up --build -d --wait
```

В PowerShell для копирования файла используйте
`Copy-Item deploy/.env.example deploy/.env`; команда `docker compose` та же,
если записать её в одну строку. При первом запуске будут собраны локальные
backend, CV и frontend; PostgreSQL, RabbitMQ и MinIO останутся зафиксированными
инфраструктурными образами. Миграции и начальные справочники выполнит
`build-watch-init`. Затем `build-watch-model-init` скачает веса `v3`, проверит
SHA-256 и поместит их в MinIO до запуска CV. Повторный запуск не загружает
совпадающую модель заново.

После запуска: интерфейс — <http://localhost:3000>, API —
<http://localhost:8000/docs>. Для остановки используйте ту же команду Compose
с `down` вместо `up --build -d --wait`. Не добавляйте
`deploy/docker-compose.submission.yaml`: он предназначен для исходного
развёртывания из GHCR и перекроет локальные имена образов.

## Веса модели

Файл `best.pt` версии `v3` хранится как публичный asset
[`model-v3`](https://github.com/build-watch-kiki/build-watch/releases/tag/model-v3),
отдельно от Git. Проверенный SHA-256, адрес и путь в MinIO записаны в
[`model-manifest.json`](model-manifest.json). `model-init` завершится с ошибкой,
если скачанный файл не совпадает с контрольной суммой; CV в этом случае не
стартует. Для собственных весов нужен новый версионированный asset и новый
manifest с его контрольной суммой.

## Существующий CI/CD

Четыре исходных репозитория и их workflows не менялись. Они продолжают
публиковать GHCR-образы и использовать свой отдельный deploy workflow.
Этот репозиторий не переключает рабочий сервер на сборку из исходников:
запуск для жюри рассчитан на отдельное чистое окружение.
