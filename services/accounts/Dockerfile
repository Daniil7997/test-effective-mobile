# --- БЛОК 1 (Общий фундамент) ---
FROM python:3.14.2-slim AS base
ENV UV_PROJECT_ENVIRONMENT="/usr/local"
ENV UV_HTTP_TIMEOUT=300
ENV UV_HTTP_RETRIES=20
WORKDIR /project
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY app/ app/
COPY migrations/ migrations/
COPY pyproject.toml .
COPY uv.lock .
COPY alembic.ini .
# (тут команды, которые нужны ВСЕМ)

# --- БЛОК 2 (Для тестов) ---
FROM base AS test
COPY tests/ tests/ 
COPY pytest.ini .
RUN uv sync --frozen --group dev 
# (тут команды ТОЛЬКО для тестов)

# --- БЛОК 3 (Для продакшена) ---
FROM base AS production
RUN uv sync --frozen --no-dev 
# (тут команды ТОЛЬКО для запуска сервера)
