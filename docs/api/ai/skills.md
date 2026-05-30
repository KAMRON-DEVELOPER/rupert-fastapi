# Skills API

Frontend API reference for the `skills` app. HTTP routes are based on the
FastAPI OpenAPI document generated from `main.py`.

## Endpoints

### Endpoint 1

- Method: `GET`
- Path: `/api/v1/skills/`
- Summary: List Skills.
- Note: Returns an array of `SkillResponse` objects. The OpenAPI response schema
  is empty.
- Query parameters:
  - `offset` (integer, optional); min 0, default 0
  - `limit` (integer, optional); min 1, max 100, default 20
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` as `PaginatedSkillResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

## Schemas

### `PaginatedSkillResponse`

Type: `object`.
Required fields: `data`, `total`.

- Fields:
  - `data` (required): `array[SkillResponse]`
  - `total` (required): `integer`

### `HTTPValidationError`

Type: `object`.

- Fields:
  - `detail` (optional): `array[ValidationError]`

### `SkillResponse`

Type: `object`.
Required fields: `id, createdAt, updatedAt, name`.

- Fields:
  - `name` (required): `string`

### `ValidationError`

Type: `object`.
Required fields: `loc`, `msg`, `type`.

- Fields:
  - `loc` (required): `array[string | integer]`
  - `msg` (required): `string`
  - `type` (required): `string`
  - `input` (optional): `Input`
  - `ctx` (optional): `object`
