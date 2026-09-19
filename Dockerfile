# syntax=docker/dockerfile:1

FROM node:22-alpine AS admin-build
WORKDIR /workspace/front/link-generator
COPY front/link-generator/package.json front/link-generator/package-lock.json ./
RUN npm ci
COPY front/link-generator/ ./
RUN npm run build

FROM ghcr.io/cirruslabs/flutter:3.44.0 AS user-build
WORKDIR /workspace/front/user
COPY front/user/pubspec.yaml front/user/pubspec.lock ./
RUN flutter pub get
COPY front/user/ ./
ARG API_BASE_URL=https://2026-da-al-g-production.up.railway.app
RUN flutter build web --release --dart-define=API_BASE_URL=${API_BASE_URL}

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl default-jre-headless fonts-noto-cjk libreoffice libreoffice-java-common \
    && rm -rf /var/lib/apt/lists/*

# LibreOffice's own HWP filter garbles these documents; H2Orestart reads them correctly
# and converts a large regulation in under a minute instead of tens of minutes.
ARG H2ORESTART_VERSION=v0.7.14
RUN curl -fsSL -o /tmp/H2Orestart.oxt \
      "https://github.com/ebandal/H2Orestart/releases/download/${H2ORESTART_VERSION}/H2Orestart.oxt" \
    && unopkg add --shared --suppress-license /tmp/H2Orestart.oxt \
    && rm /tmp/H2Orestart.oxt

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

WORKDIR /app
COPY back/pyproject.toml back/uv.lock ./back/
RUN cd back && uv sync --frozen --extra hwp --no-dev --no-install-project
COPY back/ ./back/
RUN cd back && uv sync --frozen --extra hwp --no-dev
COPY --from=admin-build /workspace/front/link-generator/dist ./admin-dist
COPY --from=user-build /workspace/front/user/build/web ./user-dist

WORKDIR /app/back
CMD ["sh", "-c", "exec /app/back/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
