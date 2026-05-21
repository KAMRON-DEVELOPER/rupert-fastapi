# RUPERT

## Installation & Project Setup

```bash
uv init rupert
cd rupert
uv add alembic basedpyright ruff black --dev
```

```bash
uv run alembic init alembic
uv run alembic revision --autogenerate -m "initial"
uv run alembic upgrade head
```

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

```bash
uv run basedpyright
uv run ruff format --check
uv run ruff format
uv run ruff check --fix
isort . && black .
black --check .
black --diff .
```

I like to know LOC so I use `cloc` tool to count line of code.

```bash
cloc --include-lang=Python src tests main.py
```
