# Companies API

Frontend API reference for the `companies` app. HTTP routes are based on the
FastAPI OpenAPI document generated from `main.py`.

## Endpoints

### Endpoint 1

- Method: `GET`
- Path: `/api/v1/companies/`
- Summary: List Companies.
- Query parameters:
  - `offset` (integer, optional); min 0, default 0
  - `limit` (integer, optional); min 1, max 100, default 20
  - `countryId` (string(uuid) | null, optional)
  - `cityId` (string(uuid) | null, optional)
  - `name` (string | null, optional)
  - `type` (CompanyType | null, optional)
  - `status` (CompanyStatus | null, optional)
  - `hasOpenVacancies` (boolean | null, optional)
- Request body (optional):
  - `application/json` as `array[string(uuid)] | null`
- Responses:
  - `200`: Successful Response; `application/json`
    `PaginatedResponse_CompanySummary_`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 2

- Method: `POST`
- Path: `/api/v1/companies/`
- Summary: Create Company.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `CompanyCreateRequest`
- Responses:
  - `201`: Successful Response; `application/json` `CompanyDetail`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 3

- Method: `GET`
- Path: `/api/v1/companies/{company_id}`
- Summary: Get Company.
- Path parameters:
  - `company_id` (string(uuid), required)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `CompanyDetail`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 4

- Method: `PATCH`
- Path: `/api/v1/companies/{company_id}`
- Summary: Update Company.
- Path parameters:
  - `company_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `CompanyUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `CompanyDetail`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 5

- Method: `DELETE`
- Path: `/api/v1/companies/{company_id}`
- Summary: Delete Company.
- Path parameters:
  - `company_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 6

- Method: `POST`
- Path: `/api/v1/companies/{company_id}/members`
- Summary: Add Company Member.
- Path parameters:
  - `company_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `CompanyMemberInviteRequest`
- Responses:
  - `201`: Successful Response; `application/json` `CompanyMemberResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 7

- Method: `PATCH`
- Path: `/api/v1/companies/{company_id}/members/{member_id}`
- Summary: Update Company Member.
- Path parameters:
  - `company_id` (string(uuid), required)
  - `member_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `CompanyMemberRoleUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `CompanyMemberResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 8

- Method: `DELETE`
- Path: `/api/v1/companies/{company_id}/members/{member_id}`
- Summary: Delete Company Member.
- Path parameters:
  - `company_id` (string(uuid), required)
  - `member_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

## Schemas

### `CityResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `countryId`, `name`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `countryId` (required): `string(uuid)`
  - `name` (required): `string`

### `CompanyCreateRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `countryId`, `name`, `type`.

- Fields:
  - `countryId` (required): `string(uuid)`
  - `cityId` (optional): `string(uuid) | null`
  - `name` (required): `string`; max length 120
  - `tagline` (optional): `string | null`
  - `description` (optional): `string | null`
  - `logoUrl` (optional): `string(uri) | null`
  - `websiteUrl` (optional): `string(uri) | null`
  - `type` (required): `CompanyType`
  - `contactEmail` (optional): `string(email) | null`
  - `contactPhone` (optional): `string | null`

### `CompanyDetail`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `country`, `city`, `name`,
`tagline`, `logoUrl`, `type`, `status`, `description`, `websiteUrl`,
`contactEmail`, `contactPhone`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `country` (required): `CountryResponse`
  - `city` (required): `CityResponse | null`
  - `name` (required): `string`
  - `tagline` (required): `string | null`
  - `logoUrl` (required): `string(uri) | null`
  - `type` (required): `CompanyType`
  - `status` (required): `CompanyStatus`
  - `openVacanciesCount` (optional): `integer | null`
  - `description` (required): `string | null`
  - `websiteUrl` (required): `string(uri) | null`
  - `contactEmail` (required): `string | null`
  - `contactPhone` (required): `string | null`
  - `memberCount` (optional): `integer | null`
  - `members` (optional): `array[CompanyMemberResponse]`

### `CompanyMemberInviteRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `userId`.

- Fields:
  - `userId` (required): `string(uuid)`
  - `role` (optional): `CompanyMemberRole`; default `member`

### `CompanyMemberResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `user`, `companyId`, `role`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `user` (required): `UserSummaryResponse`
  - `companyId` (required): `string(uuid)`
  - `role` (required): `CompanyMemberRole`

### `CompanyMemberRole`

Enum type: string.

- Values:
  - `member`
  - `recruiter`
  - `owner`

### `CompanyMemberRoleUpdateRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `role`.

- Fields:
  - `role` (required): `CompanyMemberRole`

### `CompanyStatus`

Enum type: string.

- Values:
  - `pending`
  - `approved`
  - `rejected`
  - `suspended`

### `CompanySummary`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `country`, `city`, `name`,
`tagline`, `logoUrl`, `type`, `status`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `country` (required): `CountryResponse`
  - `city` (required): `CityResponse | null`
  - `name` (required): `string`
  - `tagline` (required): `string | null`
  - `logoUrl` (required): `string(uri) | null`
  - `type` (required): `CompanyType`
  - `status` (required): `CompanyStatus`
  - `openVacanciesCount` (optional): `integer | null`

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

### `CompanyUpdateRequest`

Type: `object`.
Additional properties are not allowed.

- Fields:
  - `countryId` (optional): `string(uuid) | null`
  - `cityId` (optional): `string(uuid) | null`
  - `name` (optional): `string | null`
  - `tagline` (optional): `string | null`
  - `description` (optional): `string | null`
  - `logoUrl` (optional): `string(uri) | null`
  - `websiteUrl` (optional): `string(uri) | null`
  - `type` (optional): `CompanyType | null`
  - `contactEmail` (optional): `string(email) | null`
  - `contactPhone` (optional): `string | null`

### `CountryResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `code`, `name`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `code` (required): `string`
  - `name` (required): `string`

### `HTTPValidationError`

Type: `object`.

- Fields:
  - `detail` (optional): `array[ValidationError]`

### `JobSearchStatus`

Enum type: string.

- Values:
  - `actively_looking`
  - `open_to_offers`
  - `interviewing`
  - `not_looking`

### `MessageResponse`

Type: `object`.
Required fields: `message`.

- Fields:
  - `message` (required): `string`

### `PaginatedResponse_CompanySummary_`

Type: `object`.
Required fields: `data`, `total`.

- Fields:
  - `data` (required): `array[CompanySummary]`
  - `total` (required): `integer`

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

### `UserSummaryResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `country`, `city`, `firstName`,
`lastName`, `headline`, `avatarUrl`, `specialization`, `jobSearchStatus`,
`followersCount`, `followingsCount`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `country` (required): `CountryResponse | null`
  - `city` (required): `CityResponse | null`
  - `firstName` (required): `string`
  - `lastName` (required): `string | null`
  - `headline` (required): `string | null`
  - `avatarUrl` (required): `string | null`
  - `specialization` (required): `Specialization | null`
  - `jobSearchStatus` (required): `JobSearchStatus`
  - `followersCount` (required): `integer`
  - `followingsCount` (required): `integer`

### `ValidationError`

Type: `object`.
Required fields: `loc`, `msg`, `type`.

- Fields:
  - `loc` (required): `array[string | integer]`
  - `msg` (required): `string`
  - `type` (required): `string`
  - `input` (optional): `Input`
  - `ctx` (optional): `object`
