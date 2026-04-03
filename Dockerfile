# FROM ghcr.io/astral-sh/uv:python3.14-trixie
# FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim
FROM ghcr.io/astral-sh/uv:python3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ./pyproject.toml ./
COPY ./uv.lock ./
COPY main.py ./
COPY ./apps ./apps
COPY ./settings ./settings
COPY ./services ./services
COPY ./utility ./utility
COPY ./static ./static

RUN uv lock
RUN uv sync --locked

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]