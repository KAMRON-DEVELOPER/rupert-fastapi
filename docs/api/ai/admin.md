# Admin API

Frontend API reference for the `admin` app. HTTP routes are based on the FastAPI
OpenAPI document generated from `main.py`.

## Endpoints

### Endpoint 1

- Method: `POST`
- Path: `/api/v1/admin/locations/{country_id}/cities`
- Summary: Create City.
- Path parameters:
  - `country_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `CityRequest`
- Responses:
  - `201`: Successful Response; `application/json` as `CityResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 2

- Method: `PATCH`
- Path: `/api/v1/admin/locations/{country_id}/cities/{city_id}`
- Summary: Update City.
- Path parameters:
  - `country_id` (string(uuid), required)
  - `city_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `CityRequest`
- Responses:
  - `200`: Successful Response; `application/json` as `CityResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 3

- Method: `POST`
- Path: `/api/v1/admin/locations/countries`
- Summary: Create Country.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `CountryCreateRequest`
- Responses:
  - `201`: Successful Response; `application/json` as `CountryResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 4

- Method: `PATCH`
- Path: `/api/v1/admin/locations/countries/{country_id}`
- Summary: Update Country.
- Path parameters:
  - `country_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `CountryUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` as `CountryResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 5

- Method: `POST`
- Path: `/api/v1/admin/skills`
- Summary: Create Skill.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `SkillRequest`
- Responses:
  - `201`: Successful Response; `application/json` as `SkillResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 6

- Method: `PATCH`
- Path: `/api/v1/admin/skills/{skill_id}`
- Summary: Update Skill.
- Path parameters:
  - `skill_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `SkillRequest`
- Responses:
  - `200`: Successful Response; `application/json` as `SkillResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 7

- Method: `DELETE`
- Path: `/api/v1/admin/locations/{country_id}/cities/{city_id}`
- Summary: Delete City.
- Path parameters:
  - `country_id` (string(uuid), required)
  - `city_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Responses:
  - `204`: Successful Response
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 8

- Method: `DELETE`
- Path: `/api/v1/admin/locations/countries/{country_id}`
- Summary: Delete Country.
- Path parameters:
  - `country_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Responses:
  - `204`: Successful Response
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 9

- Method: `DELETE`
- Path: `/api/v1/admin/skills/{skill_id}`
- Summary: Delete Skill.
- Path parameters:
  - `skill_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Responses:
  - `204`: Successful Response
  - `422`: Validation Error; `application/json` `HTTPValidationError`

## Schemas

### `CityRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `name`.

- Fields:
  - `name` (required): `string`; max length 168

### `CountryCreateRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `code`, `name`.

- Fields:
  - `code` (required): `string`; max length 2
  - `name` (required): `string`; max length 56

### `CountryUpdateRequest`

Type: `object`.
Additional properties are not allowed.

- Fields:
  - `code` (optional): `string | null`
  - `name` (optional): `string | null`

### `HTTPValidationError`

Type: `object`.

- Fields:
  - `detail` (optional): `array[ValidationError]`

### `SkillRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `name`.

- Fields:
  - `name` (required): `string`; max length 64

### `ValidationError`

Type: `object`.
Required fields: `loc`, `msg`, `type`.

- Fields:
  - `loc` (required): `array[string | integer]`
  - `msg` (required): `string`
  - `type` (required): `string`
  - `input` (optional): `Input`
  - `ctx` (optional): `object`
