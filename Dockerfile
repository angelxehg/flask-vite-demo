ARG STATIC_URL=""
ARG VITE_BASE_PATH="/"

# Builds the frontend natively on the build host regardless of which
# platform(s) the final image targets: JS/CSS output isn't
# architecture-specific, so this avoids running `npm run build` once per arch.
FROM --platform=$BUILDPLATFORM node:24-slim AS frontend-build
ARG VITE_BASE_PATH
ENV VITE_BASE_PATH=${VITE_BASE_PATH}
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Nothing but the build output, so CI's
# `docker buildx build --target assets --output type=local` writes the
# hashed asset files straight into a destination directory with no
# path-juggling, ready to sync to S3.
FROM scratch AS assets
COPY --from=frontend-build /app/src/flask_vite_demo/static/dist /

FROM python:3.14-slim AS base

# Kamal refuses to deploy an image whose `service` label does not match the
# `service:` in its config, and it checks on every deploy with no way to skip.
# Kamal sets this label itself when it builds; this image is built here and only
# pulled there, so it has to be set here. It must stay in step with
# config/flask-vite-demo/deploy.yml in the infra repository.
LABEL service="flask-vite-demo"

# Baked in at build time so a pushed image already knows where its own assets
# live, with no runtime configuration required from Kamal/infra. Empty by
# default: the app then falls back to serving its own bundled assets and the
# CSP stays self-only, which is what local/dev use wants.
ARG STATIC_URL
ENV STATIC_URL=${STATIC_URL}

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src ./src
# Overwrites whatever COPY src ./src brought in with the fresh, arg-consistent
# build from the frontend-build stage above.
COPY --from=frontend-build /app/src/flask_vite_demo/static/dist ./src/flask_vite_demo/static/dist
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "flask_vite_demo.app:create_app()"]
