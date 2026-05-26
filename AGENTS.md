# FastAPI Project Rules and Architecture Conventions

This document defines the working rules for AI coding agents contributing to this
FastAPI codebase.

The project uses a pragmatic layered architecture. The current conventions are still
evolving, and some existing code may contain gaps, quirks, or imperfect trade-offs.
Prefer following the patterns already present in the codebase over inventing cleaner
but incompatible abstractions. The goal is to ship useful, maintainable changes
without over-engineering or destabilizing working code.

## Agent Role

You are working as an autonomous senior engineer inside a large FastAPI codebase.

Once the user gives a direction, proactively gather context, plan, implement,
and refine. Do not wait for repeated prompts unless the requirement is genuinely
ambiguous or a change would be risky without confirmation.

Optimize for correctness, clarity, reliability, and consistency with the existing
project.

## Repository Shape

Typical project layout:

```text
src/
├── apps/
│   ├── <domain>/
│   │   ├── models.py
│   │   ├── repositories/
│   │   ├── routes/
│   │   └── schemas/
│   ├── shared/
│   │   ├── models/
│   │   └── schemas/
│   └── ...
├── core/
├── dependencies/
├── middlewares/
└── services/
tests/
├── integration/
└── unit/
```

Domain apps usually contain:

- `routes/` for FastAPI path operation functions.
- `schemas/` for Pydantic request, response, dependency, and parameter schemas.
- `repositories/` for database access and persistence logic.
- `models.py` for SQLAlchemy models.

Some older or smaller apps may use flatter files such as `routes.py`, `schemas.py`,
or `repositories.py`. Follow the local pattern of the app you are editing.

## Architecture Rules

Use the existing layered style. Do not mix responsibilities between layers.

### Routes Layer

Path operation functions belong in `src/apps/<domain>/routes/`.

Routes should:

- Define FastAPI endpoints, dependencies, request bodies, path/query parameters,
and response models.
- Extract authenticated user data from dependencies such as `authDep` or `authProbeDep`.
- Call repository methods for business/database operations.
- Commit the session after successful write operations.
- Convert ORM records into response schemas using `model_validate(...)` when appropriate.
- Return `MessageResponse` for simple successful mutation messages when that is
the existing pattern.

Routes should not:

- Contain complex database queries.
- Perform authorization checks that already belong in repositories.
- Directly manipulate SQLAlchemy models beyond passing data to repositories.
- Introduce new service abstractions unless the surrounding code already uses them.

Example route style:

```python
@vacancies_router.patch("/{id}", response_model=VacancyDetail)
async def update_vacancy(
    auth: authDep,
    session: sessionDep,
    id: Annotated[UUID, Path()],
    schm: VacancyUpdateRequest,
):
    user_id, _, _ = auth
    record = await VacanciesRepository.update(
        session,
        user_id,
        id,
        schm.model_dump(mode="json", exclude_unset=True),
    )
    await session.commit()
    return VacancyDetail.model_validate(record)
```

### Schemas Layer

Pydantic schemas belong in `src/apps/<domain>/schemas/`.

Schemas should:

- Define request, response, list-filter, and dependency models.
- Use `Field(...)` constraints for simple validation.
- Use `field_validator` for cross-field or custom validation.
- Use existing shared base schemas such as `RequestSchema`, `BaseModelResponse`,
`BaseNullableLocationModelResponse`, `PaginatedResponse`, and pagination dependencies.
- Use `Annotated[..., Depends(...)]` aliases for dependency schemas when the codebase
already does this.

Schemas should not:

- Execute database queries.
- Perform persistence.
- Contain business workflows that belong in repositories.

For multipart form endpoints, follow the existing `as_form` classmethod pattern
when needed.

### Repository Layer

Repository classes belong in `src/apps/<domain>/repositories/`.

Repositories should:

- Own SQLAlchemy query construction and execution.
- Perform database-backed validation and authorization checks.
- Use `select`, `update`, `delete`, `exists`, `func`, and loader options directly.
- Use `selectinload` for relationships when response schemas need related data.
- Raise `HTTPException` with appropriate status codes for not-found, forbidden,
conflict, and invalid-operation cases.
- Catch expected SQLAlchemy errors such as `IntegrityError` where useful.
- Log unexpected exceptions using the existing logger.
- Roll back the session inside exception handlers when a repository method performed
writes.
- Return ORM records or existing response-shaped objects according to the surrounding
pattern.

Repositories should not:

- Commit the session. Routes commit after successful writes.
- Define FastAPI route dependencies.
- Define Pydantic schemas.
- Introduce unrelated abstractions or generic repository frameworks.

Example repository style:

```python
class UsersRepository:
    @staticmethod
    async def update(session: AsyncSession, id: UUID, values: dict):
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values(values)
            .returning(UserModel.id)
        )

        try:
            updated_id = await session.scalar(stmt)

            if not updated_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User not found to update",
                )

            await session.flush()
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"[UsersRepository] update: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while updating user",
            )
```

### Models Layer

SQLAlchemy models live in `models.py` files or shared model modules.

In normal feature work, assume models are already created by the project owner.
Do not modify SQLAlchemy models unless the task explicitly requires a schema/model
change or the existing model is clearly blocking the requested feature.

Before touching a model:

1. Confirm the requested behavior cannot be implemented through routes, schemas,
and repositories alone.
2. Check whether migrations are required.
3. Keep model changes minimal and consistent with existing field, enum, relationship,
and naming patterns.

## Current Project Conventions

### Dependencies

Use existing dependency aliases and imports:

- `sessionDep` from `src.core.database`
- `authDep` and `authProbeDep` from `src.dependencies.proactive_refresh`
- `paginationDep` from shared schemas

### Request Data

For create requests, use `schm.model_dump(...)` according to local context.

Common patterns:

```python
schm.model_dump()
schm.model_dump(mode="json")
schm.model_dump(exclude_unset=True)
schm.model_dump(mode="json", exclude_unset=True)
```

Use `exclude_unset=True` for PATCH/update operations so omitted fields are not overwritten.

Use `mode="json"` when the repository or SQLAlchemy operation expects JSON-compatible
values, especially for Pydantic types such as URLs or enums where existing code
already uses this mode.

### Responses

Use declared `response_model` in routes.

When returning ORM objects, validate with the appropriate schema:

```python
return VacancyDetail.model_validate(record)
```

For paginated list endpoints, return `PaginatedResponse[...]` as already used in
the domain.

### Transactions

Routes commit after successful writes:

```python
await session.commit()
```

Repositories flush but generally do not commit:

```python
await session.flush()
```

Repositories may roll back on write failures:

```python
await session.rollback()
```

### Errors

Use `HTTPException` for API-facing errors.

Prefer status codes already used in the codebase:

- `400 BAD_REQUEST` for invalid operation or failed update precondition.
- `404 NOT_FOUND` for missing resources.
- `409 CONFLICT` for uniqueness or integrity conflicts.
- `500 INTERNAL_SERVER_ERROR` for unexpected failures.

## Coding Standards

### Python Style

Follow the existing codebase style:

- Python async/await.
- Type hints for function parameters and returns where practical.
- Static repository methods in repository classes.
- Clear local variable names.
- Existing import grouping and formatting.
- Existing enum and schema names.
- Existing router naming conventions.

### Search and File Reading

When searching the repository:

- Prefer `rg` for text search.
- Prefer `rg --files` for file discovery.
- If `rg` is unavailable, use the closest available alternative.

When a dedicated file-reading or code-editing tool exists, prefer that tool over
raw shell commands.

Read enough context before editing. Avoid repeated micro-edits. Batch related changes
into coherent patches.
