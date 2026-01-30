FROM python:3.12 as base

ARG DEV=false
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8


FROM base as builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Install system dependencies including locales
RUN apt-get update && apt-get install -y \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Generate and set locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Install Poetry
RUN pip install poetry

# Install the app
COPY pyproject.toml poetry.lock ./

RUN poetry install --with dev --no-root && rm -rf $POETRY_CACHE_DIR;

FROM base as runtime

RUN apt-get update && apt-get install -y \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Generate and set locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8
COPY --from=builder /app /app

WORKDIR /app
COPY templates/ ./templates/
COPY app/ ./app/
COPY .env ./

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
