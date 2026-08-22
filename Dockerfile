FROM python:3.14-slim AS base

# Kamal refuses to deploy an image whose `service` label does not match the
# `service:` in its config, and it checks on every deploy with no way to skip.
# Kamal sets this label itself when it builds; this image is built here and only
# pulled there, so it has to be set here. It must stay in step with
# config/flask-vite-demo/deploy.yml in the infra repository.
LABEL service="flask-vite-demo"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src ./src
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "flask_vite_demo.app:create_app()"]
