# Locations API

Frontend API reference for the `locations` app. HTTP routes are based on the
FastAPI OpenAPI document generated from `main.py`.

## Endpoints

### Endpoint 1

- Method: `GET`
- Path: `/api/v1/locations/locations/countries`
- Summary: List Countries.
- Query parameters:
  - `offset` (integer, optional); min 0, default 0
  - `limit` (integer, optional); min 1, max 100, default 20
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` as `PaginatedCountryResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 2

- Method: `GET`
- Path: `/api/v1/locations/locations/countries/{country_id}/cities`
- Summary: List Cities.
- Path parameters:
  - `country_id` (string(uuid), required)
- Query parameters:
  - `offset` (integer, optional); min 0, default 0
  - `limit` (integer, optional); min 1, max 100, default 20
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` as `PaginatedCityResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

## Schemas

### `PaginatedCountryResponse`

Type: `object`.
Required fields: `data`, `total`.

- Fields:
  - `data` (required): `array[CountryResponse]`
  - `total` (required): `integer`

### `PaginatedCityResponse`

Type: `object`.
Required fields: `data`, `total`.

- Fields:
  - `data` (required): `array[CityResponse]`
  - `total` (required): `integer`

### `CityResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `countryId`, `name`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `countryId` (required): `string(uuid)`
  - `name` (required): `string`

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

### `ValidationError`

Type: `object`.
Required fields: `loc`, `msg`, `type`.

- Fields:
  - `loc` (required): `array[string | integer]`
  - `msg` (required): `string`
  - `type` (required): `string`
  - `input` (optional): `Input`
  - `ctx` (optional): `object`
