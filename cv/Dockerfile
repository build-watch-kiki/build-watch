FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_LINK_MODE=copy

# Системные библиотеки для opencv-python (зависимость ultralytics).
# Без них `import cv2` падает: libxcb.so.1: cannot open shared object file.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 libsm6 libxext6 libxrender1 libxcb1 \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY buildwatchcv ./buildwatchcv

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["faststream", "run", "buildwatchcv.main:app"]
