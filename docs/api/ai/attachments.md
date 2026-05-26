# Attachments API

Frontend API reference for the `attachments` app. HTTP routes are based on the
FastAPI OpenAPI document generated from `main.py`.

## Endpoints

### Endpoint 1

- Method: `POST`
- Path: `/api/v1/attachments/`
- Summary: Upload Attachments.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `multipart/form-data` as `Body_upload_attachments_api_v1_attachments__post`
- Responses:
  - `200`: Successful Response; `application/json` `UploadAttachmentsResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 2

- Method: `DELETE`
- Path: `/api/v1/attachments/`
- Summary: Delete Attachments.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `array[string(uuid)]`
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

## Schemas

### `AttachmentStatus`

Enum type: string.

- Values:
  - `pending`
  - `ready`

### `AttachmentWithPositionableResponse`

Type: `object`.
Required fields: `id`, `objectKey`, `originalFilename`, `status`, `mimeType`,
`label`, `group`, `sizeBytes`, `isPositionable`, `url`.

- Fields:
  - `id` (required): `string(uuid)`
  - `objectKey` (required): `string`
  - `originalFilename` (required): `string | null`
  - `status` (required): `AttachmentStatus`
  - `mimeType` (required): `string`
  - `label` (required): `string`
  - `group` (required): `string`
  - `sizeBytes` (required): `integer`
  - `meta` (optional): `object`
  - `isPositionable` (required): `boolean`
  - `url` (required): `string`; read-only

### `Body_upload_attachments_api_v1_attachments__post`

Type: `object`.
Required fields: `files`.

- Fields:
  - `files` (required): `array[string]`

### `HTTPValidationError`

Type: `object`.

- Fields:
  - `detail` (optional): `array[ValidationError]`

### `UploadAttachmentsResponse`

Type: `object`.
Required fields: `attachments`, `failed`.

- Fields:
  - `attachments` (required): `array[AttachmentWithPositionableResponse]`
  - `failed` (required): `array[string]`

### `ValidationError`

Type: `object`.
Required fields: `loc`, `msg`, `type`.

- Fields:
  - `loc` (required): `array[string | integer]`
  - `msg` (required): `string`
  - `type` (required): `string`
  - `input` (optional): `Input`
  - `ctx` (optional): `object`
