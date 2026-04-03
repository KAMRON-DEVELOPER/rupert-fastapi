# RUPERT

## Installation & Project Setup

```bash
uv init rupert
cd rupert
uv add alembic basedpyright ruff black --dev
```

```bash
alembic init alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```
