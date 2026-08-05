---
name: repo-normalization
description: Normalize FastAPI repository layer to RUPERT standard — enforce method order create→update→delete→get_many→get→get_optional, fix error handling with IntegrityError rollback + logging, rename legacy methods, preserve domain extras, and update route call sites. Use when normalizing or reviewing src/apps/*/repositories/* files.
---

# Repository Normalization Skill

Use this skill when you need to normalize repository classes in `src/apps/<domain>/repositories/` to the project standard defined in `src/apps/users/repositories/resume.py` (ResumesRepository golden standard).

## When to Use

- User asks to normalize repository layer across domains
- Adding a new domain app and need consistent repository pattern
- Found copy-paste bugs in repository logs or returning clauses
- Route files have signature mismatches with repositories
- Method names like `get_by_id`, `get_applications`, `list_by_user_id` need renaming to standard

## Golden Standard Reference

`src/apps/users/repositories/resume.py` — `ResumesRepository`:

- `create`: `insert(Model).values(...).returning(Model).options(*OPTIONS)` + `try/except IntegrityError` + `rollback` + `logger.error("[Repo] create integrity: {e}")` + `409 CONFLICT` + generic `Exception` branch.
- `update`: `update(Model).where(...).values(...).returning(Model).options(*OPTIONS)` + `NoResultFound → 404` + `IntegrityError` handling + generic `Exception`.
- `delete`: `delete(Model).where(...).returning(Model.id)` + `NoResultFound → 404` + generic `Exception` + rollback + log.
- `get_many`: `select(...).where(...).order_by(...).offset().limit()` + total count + `PaginatedResponse` + generic `Exception` log.
- `get`: `select(Model).options(*OPTIONS).where(...)` + `.one()` + `NoResultFound → 404`, `MultipleResultsFound → 500`, generic `Exception`.
- `get_optional`: `select(...).where(...)` + `scalar()` returns `None` if not found + generic `Exception`.

All `create/update/delete` must have rollback on failure. All log messages must use correct repo name `[ClassName] method`.

## Step-by-Step Workflow

### 1. Exploration
- Glob `src/apps/<domain>/repositories/*.py`
- Read each file, note current method order, missing core methods, legacy names, log prefix errors, empty `.returning()` or duplicate try/except.
- Read corresponding `src/apps/<domain>/routes/*.py` to capture call sites for renames.
- Read golden standard `src/apps/users/repositories/resume.py`.

### 2. Spec Per Domain
For each repository class:
- Target order: `create → update → delete → get_many → get → get_optional → <domain-specific extras>`
- Extras must be preserved — never delete domain logic (`_enforce_ownership`, `set_email_verified`, `ensure_member`, etc.).
- Renames:
  - `get_by_id` → `get`
  - `get_applications` → `get_many`
  - `list_by_user_id` → `get_many`
  - `get_by_id_and_user_id` → split into `get` (raises 404) + `get_optional` (returns None)
- Missing methods to add if absent: `get`, `get_optional`, `get_many` where paginated.
- Error handling to normalize: add `IntegrityError` catch to all `create/update/delete`, ensure `rollback()` + `logger.error(f"[RepoName] method: {e}")`.

Copy-paste bug checklist (critical in `src/apps/vacancies/repositories/application.py` precedent):
- Log says `[ResumesRepository]` or `[ChatRepository]` instead of own class → fix
- Error detail says "Resume" instead of own entity → fix
- `.returning()` with empty args → should be `.returning(Model).options(*OPTIONS)` or `.returning(Model.id)`
- Duplicate unreachable `try/except` after first block → remove
- Missing `vacancy_id` / other filters in `where` clause for update

### 3. Implementation (Parallelizable)
- Reorder methods in each file.
- Add missing methods.
- Fix error handling + log prefixes.
- Do not change models — assume models exist.
- Preserve `OPTIONS = (selectinload(...))` pattern.

### 4. Route Updates
- After renaming, grep for old names: `grep -rn "get_by_id\|get_applications" src/apps/<domain>/`
- Update all call sites in `src/apps/<domain>/routes/`.
- Verify signatures: route params must match repository params (`user_id`, `id`, `offset/limit`, etc.). Check precedent bug where `vacancy_id=` was passed but repo expected `application_id=`.

### 5. Validation
```
.venv/bin/ruff check src/apps/<domain>/repositories/ src/apps/<domain>/routes/
python -m py_compile src/apps/<domain>/repositories/*.py
```
- Ensure no stale `get_by_id` references in normalized domains (except allowed internal helpers in follow.py etc).
- Run `basedpyright` on key files if type errors suspected.

## Output Checklist

- [ ] Methods ordered `create → update → delete → get_many → get → get_optional → extras`
- [ ] `get` raises 404 via `NoResultFound`, `get_optional` returns None
- [ ] All `create/update/delete` have `IntegrityError + rollback + logger.error + 409` + generic `Exception + rollback + logger.error + 500`
- [ ] Log prefixes corrected to `[RepoClassName]`
- [ ] Legacy renames done + route call sites updated
- [ ] Extras preserved
- [ ] `ruff check` clean, `py_compile` OK
- [ ] No empty `.returning()` or duplicate try blocks

## Edge Cases

- `SessionsRepository`, `FollowsRepository`, `OAuthUsersRepository` have non-standard extra semantics — keep their domain methods but still add `get/get_optional` if missing.
- `UserSkill`, `ResumeSkill`, `VacancySkill` repositories need ownership checks (`_enforce_ownership`) — keep private helpers after core methods.
- If route commit pattern broken (repo commits instead of flush) — fix: repos flush, routes commit via `await session.commit()`.

## References

- Golden: `src/apps/users/repositories/resume.py`
- Examples normalized: `src/apps/companies/repositories/company.py`, `src/apps/vacancies/repositories/vacancy.py`, `src/apps/vacancies/repositories/application.py`
- Routes: `src/apps/companies/routes/company.py`, `src/apps/vacancies/routes/vacancy.py`, `src/apps/vacancies/routes/application.py`
- Project rules: `MEMORY.md` §Rules + `AGENTS.md` Architecture Rules
