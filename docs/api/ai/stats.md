# Stats API

Frontend API reference for the `stats` app. HTTP routes are based on the FastAPI
OpenAPI document generated from `main.py`.

## Endpoints

### Endpoint 1

- Method: `GET`
- Path: `/api/v1/stats/`
- Summary: Stats.
- Note: Returns `Stats`. The route currently omits a `response_model`, so
  OpenAPI shows an empty response schema.
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` not specified

## Schemas

### `CompaniesStats`

Type: `object`.
Required fields: `total`, `by_type`.

- Fields:
  - `total` (required): `integer`
  - `by_type` (required): `array[CompanyTypeBucket]`

### `CompanyType`

Enum type: string.

- Values:
  - `startup`
  - `product_company`
  - `agency`
  - `outsourcing`
  - `outstaffing`
  - `enterprise`
  - `government`

### `CompanyTypeBucket`

Type: `object`.
Required fields: `count`, `percentage`, `key`.

- Fields:
  - `count` (required): `integer`
  - `percentage` (required): `number`
  - `key` (required): `CompanyType`

### `DailyActiveUsersBucket`

Type: `object`.
Required fields: `count`, `date`.

- Fields:
  - `count` (required): `integer`
  - `date` (required): `string(date)`

### `JobSearchStatus`

Enum type: string.

- Values:
  - `actively_looking`
  - `open_to_offers`
  - `interviewing`
  - `not_looking`

### `JobSearchStatusBucket`

Type: `object`.
Required fields: `count`, `percentage`, `key`.

- Fields:
  - `count` (required): `integer`
  - `percentage` (required): `number`
  - `key` (required): `JobSearchStatus`

### `Specialization`

Enum type: string.

- Values:
  - `frontend`
  - `backend`
  - `fullstack`
  - `ios`
  - `android`
  - `cross_platform_mobile`
  - `desktop`
  - `embedded`
  - `systems`
  - `firmware`
  - `devops`
  - `platform`
  - `sre`
  - `cloud`
  - `data_engineering`
  - `data_science`
  - `machine_learning`
  - `ai_engineering`
  - `data_analytics`
  - `security`
  - `application_security`
  - `blockchain`
  - `game`
  - `qa`
  - `ui_ux`
  - `developer_relations`
  - `technical_writing`

### `SpecializationBucket`

Type: `object`.
Required fields: `count`, `percentage`, `key`.

- Fields:
  - `count` (required): `integer`
  - `percentage` (required): `number`
  - `key` (required): `Specialization`

### `Stats`

Type: `object`.
Required fields: `users`, `vacancies`, `companies`.

- Fields:
  - `users` (required): `UsersStats`
  - `vacancies` (required): `VacanciesStats`
  - `companies` (required): `CompaniesStats`

### `UsersStats`

Type: `object`.
Required fields: `total`, `looking_for_job_count`, `looking_for_job_percentage`,
`dau_chart`, `by_job_search_status`, `by_specialization`.

- Fields:
  - `total` (required): `integer`
  - `looking_for_job_count` (required): `integer`
  - `looking_for_job_percentage` (required): `number`
  - `dau_chart` (required): `array[DailyActiveUsersBucket]`
  - `by_job_search_status` (required): `array[JobSearchStatusBucket]`
  - `by_specialization` (required): `array[SpecializationBucket]`

### `VacanciesStats`

Type: `object`.
Required fields: `total`, `open`, `by_status`, `by_specialization`.

- Fields:
  - `total` (required): `integer`
  - `open` (required): `integer`
  - `by_status` (required): `array[VacancyStatusBucket]`
  - `by_specialization` (required): `array[SpecializationBucket]`

### `VacancyStatus`

Enum type: string.

- Values:
  - `draft`
  - `open`
  - `archived`
  - `closed`

### `VacancyStatusBucket`

Type: `object`.
Required fields: `count`, `percentage`, `key`.

- Fields:
  - `count` (required): `integer`
  - `percentage` (required): `number`
  - `key` (required): `VacancyStatus`
