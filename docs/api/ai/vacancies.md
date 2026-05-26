# Vacancies API

Frontend API reference for the `vacancies` app. HTTP routes are based on the
FastAPI OpenAPI document generated from `main.py`.

## Endpoints

### Endpoint 1

- Method: `GET`
- Path: `/api/v1/vacancies/`
- Summary: List Vacancies.
- Query parameters:
  - `offset` (integer, optional); min 0, default 0
  - `limit` (integer, optional); min 1, max 100, default 20
  - `companyId` (string(uuid) | null, optional)
  - `title` (string | null, optional)
  - `submissionType` (SubmissionType | null, optional)
  - `specialization` (Specialization | null, optional)
  - `salaryMin` (integer | null, optional)
  - `salaryMax` (integer | null, optional)
  - `salaryCurrency` (SalaryCurrency | null, optional)
  - `yearsOfExperienceMin` (number | null, optional)
  - `workFormat` (WorkFormat | null, optional)
  - `employmentType` (EmploymentType | null, optional)
  - `status` (VacancyStatus | null, optional)
  - `countryId` (string(uuid) | null, optional)
  - `cityId` (string(uuid) | null, optional)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (optional):
  - `application/json` as `array[string(uuid)] | null`
- Responses:
  - `200`: Successful Response; `application/json`
    `PaginatedResponse_VacancySummary_`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 2

- Method: `GET`
- Path: `/api/v1/vacancies/applications`
- Summary: List Applications.
- Query parameters:
  - `offset` (integer, optional); min 0, default 0
  - `limit` (integer, optional); min 1, max 100, default 20
  - `vacancyId` (string(uuid) | null, optional)
  - `applicantId` (string(uuid) | null, optional)
  - `status` (ApplicationStatus | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json`
    `PaginatedResponse_ApplicationSummary_`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 3

- Method: `POST`
- Path: `/api/v1/vacancies/applications`
- Summary: Apply To Vacancy.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `ApplicationRequest`
- Responses:
  - `201`: Successful Response; `application/json` `ApplicationDetail`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 4

- Method: `GET`
- Path: `/api/v1/vacancies/applications/{id}`
- Summary: Get Application.
- Path parameters:
  - `id` (string(uuid), required)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `ApplicationDetail`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 5

- Method: `PATCH`
- Path: `/api/v1/vacancies/applications/{id}`
- Summary: Update Application Status.
- Path parameters:
  - `id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `ApplicationStatusUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `ApplicationDetail`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 6

- Method: `POST`
- Path: `/api/v1/vacancies/companies/{company_id}`
- Summary: Create Vacancy.
- Path parameters:
  - `company_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `VacancyCreateRequest`
- Responses:
  - `201`: Successful Response; `application/json` `VacancyDetail`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 7

- Method: `GET`
- Path: `/api/v1/vacancies/{id}`
- Summary: Get Vacancy.
- Path parameters:
  - `id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `VacancyDetail`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 8

- Method: `PATCH`
- Path: `/api/v1/vacancies/{id}`
- Summary: Update Vacancy.
- Path parameters:
  - `id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `VacancyUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `VacancyDetail`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 9

- Method: `DELETE`
- Path: `/api/v1/vacancies/{id}`
- Summary: Delete Vacancy.
- Path parameters:
  - `id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 10

- Method: `POST`
- Path: `/api/v1/vacancies/{vacancy_id}/skills`
- Summary: Create Vacancy Skill.
- Path parameters:
  - `vacancy_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `VacancySkillLinkRequest`
- Responses:
  - `201`: Successful Response; `application/json` `VacancySkillLinkResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 11

- Method: `PATCH`
- Path: `/api/v1/vacancies/{vacancy_id}/skills/{skill_link_id}`
- Summary: Update Vacancy Skill.
- Path parameters:
  - `vacancy_id` (string(uuid), required)
  - `skill_link_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `VacancySkillLinkUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `VacancySkillLinkResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 12

- Method: `DELETE`
- Path: `/api/v1/vacancies/{vacancy_id}/skills/{skill_link_id}`
- Summary: Delete Vacancy Skill.
- Path parameters:
  - `vacancy_id` (string(uuid), required)
  - `skill_link_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 13

- Method: `POST`
- Path: `/api/v1/vacancies/{id}/save`
- Summary: Save Vacancy.
- Path parameters:
  - `id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 14

- Method: `DELETE`
- Path: `/api/v1/vacancies/{id}/save`
- Summary: Unsave Vacancy.
- Path parameters:
  - `id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

## Schemas

### `ApplicationDetail`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `vacancyId`, `applicantId`,
`status`, `coverLetter`, `vacancy`, `resume`, `applicant`, `recruiterNote`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `vacancyId` (required): `string(uuid)`
  - `applicantId` (required): `string(uuid)`
  - `status` (required): `ApplicationStatus`
  - `coverLetter` (required): `string | null`
  - `vacancy` (required): `VacancySummary`
  - `resume` (required): `ResumeSummary | null`
  - `applicant` (required): `UserSummaryResponse`
  - `recruiterNote` (required): `string | null`

### `ApplicationRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `vacancyId`.

- Fields:
  - `vacancyId` (required): `string(uuid)`
  - `resumeId` (optional): `string(uuid) | null`
  - `coverLetter` (optional): `string | null`

### `ApplicationStatus`

Enum type: string.

- Values:
  - `pending`
  - `viewed`
  - `shortlisted`
  - `interview`
  - `offer`
  - `rejected`
  - `hired`

### `ApplicationStatusUpdateRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `status`.

- Fields:
  - `status` (required): `ApplicationStatus`
  - `recruiterNote` (optional): `string | null`

### `ApplicationSummary`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `vacancyId`, `applicantId`,
`status`, `coverLetter`, `vacancy`, `resume`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `vacancyId` (required): `string(uuid)`
  - `applicantId` (required): `string(uuid)`
  - `status` (required): `ApplicationStatus`
  - `coverLetter` (required): `string | null`
  - `vacancy` (required): `VacancySummary`
  - `resume` (required): `ResumeSummary | null`

### `CityResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `countryId`, `name`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `countryId` (required): `string(uuid)`
  - `name` (required): `string`

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

### `CountryResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `code`, `name`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `code` (required): `string`
  - `name` (required): `string`

### `EmploymentType`

Enum type: string.

- Values:
  - `full_time`
  - `part_time`
  - `contract`
  - `internship`

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

### `PaginatedResponse_ApplicationSummary_`

Type: `object`.
Required fields: `data`, `total`.

- Fields:
  - `data` (required): `array[ApplicationSummary]`
  - `total` (required): `integer`

### `PaginatedResponse_VacancySummary_`

Type: `object`.
Required fields: `data`, `total`.

- Fields:
  - `data` (required): `array[VacancySummary]`
  - `total` (required): `integer`

### `PaymentFrequency`

Enum type: string.

- Values:
  - `hourly`
  - `daily`
  - `once_a_week`
  - `twice_a_month`
  - `once_a_month`
  - `per_project`

### `ProficiencyLevel`

Enum type: string.

- Values:
  - `beginner`
  - `intermediate`
  - `advanced`
  - `expert`

### `ResumeSummary`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `country`, `city`, `userId`,
`title`, `specialization`, `salaryExpectationMin`, `salaryExpectationMax`,
`salaryCurrency`, `workFormat`, `employmentType`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `country` (required): `CountryResponse`
  - `city` (required): `CityResponse | null`
  - `userId` (required): `string(uuid)`
  - `title` (required): `string`
  - `specialization` (required): `Specialization`
  - `salaryExpectationMin` (required): `integer | null`
  - `salaryExpectationMax` (required): `integer | null`
  - `salaryCurrency` (required): `SalaryCurrency | null`
  - `workFormat` (required): `WorkFormat | null`
  - `employmentType` (required): `EmploymentType | null`

### `SalaryCurrency`

Enum type: string.

- Values:
  - `UZS`
  - `KZT`
  - `KGS`
  - `TJS`
  - `TMT`
  - `USD`
  - `EUR`
  - `TRY`

### `SkillResponse`

Type: `object`.
Required fields: `name`.

- Fields:
  - `name` (required): `string`

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

### `SubmissionType`

Enum type: string.

- Values:
  - `profile`
  - `resume`

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

### `VacancyCreateRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `countryId`, `title`, `description`, `submissionType`,
`specialization`.

- Fields:
  - `countryId` (required): `string(uuid)`
  - `cityId` (optional): `string(uuid) | null`
  - `title` (required): `string`; max length 128
  - `description` (required): `string`
  - `externalApplyUrl` (optional): `string(uri) | null`
  - `submissionType` (required): `SubmissionType`
  - `specialization` (required): `Specialization`
  - `salaryMin` (optional): `integer | null`
  - `salaryMax` (optional): `integer | null`
  - `salaryCurrency` (optional): `SalaryCurrency | null`
  - `paymentFrequency` (optional): `PaymentFrequency | null`
  - `yearsOfExperienceMin` (optional): `number | null`
  - `workFormat` (optional): `WorkFormat`; default `onsite`
  - `workHoursPerWeek` (optional): `integer | null`
  - `employmentType` (optional): `EmploymentType`; default `full_time`
  - `status` (optional): `VacancyStatus`; default `draft`
  - `skills` (optional): `array[VacancySkillLinkRequest]`

### `VacancyDetail`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `country`, `city`, `company`,
`title`, `submissionType`, `specialization`, `salaryMin`, `salaryMax`,
`salaryCurrency`, `workFormat`, `employmentType`, `status`, `description`,
`externalApplyUrl`, `paymentFrequency`, `skillLinks`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `country` (required): `CountryResponse`
  - `city` (required): `CityResponse | null`
  - `company` (required): `CompanySummary`
  - `title` (required): `string`
  - `submissionType` (required): `SubmissionType`
  - `specialization` (required): `Specialization`
  - `salaryMin` (required): `integer | null`
  - `salaryMax` (required): `integer | null`
  - `salaryCurrency` (required): `SalaryCurrency | null`
  - `yearsOfExperienceMin` (optional): `number | null`
  - `workFormat` (required): `WorkFormat`
  - `employmentType` (required): `EmploymentType`
  - `status` (required): `VacancyStatus`
  - `isSaved` (optional): `boolean | null`
  - `hasApplied` (optional): `boolean | null`
  - `description` (required): `string`
  - `externalApplyUrl` (required): `string(uri) | null`
  - `workHoursPerWeek` (optional): `integer | null`
  - `paymentFrequency` (required): `PaymentFrequency | null`
  - `skillLinks` (required): `array[VacancySkillLinkResponse]`

### `VacancySkillLinkRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `skillId`, `proficiency`.

- Fields:
  - `skillId` (required): `string(uuid)`
  - `proficiency` (required): `ProficiencyLevel`
  - `yearsOfExperienceMin` (optional): `number | null`
  - `isRequired` (optional): `boolean`; default `true`

### `VacancySkillLinkResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `vacancyId`, `skill`,
`proficiency`, `yearsOfExperienceMin`, `isRequired`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `vacancyId` (required): `string(uuid)`
  - `skill` (required): `SkillResponse`
  - `proficiency` (required): `ProficiencyLevel`
  - `yearsOfExperienceMin` (required): `number | null`
  - `isRequired` (required): `boolean`

### `VacancySkillLinkUpdateRequest`

Type: `object`.
Additional properties are not allowed.

- Fields:
  - `proficiency` (optional): `ProficiencyLevel | null`
  - `yearsOfExperienceMin` (optional): `number | null`
  - `isRequired` (optional): `boolean | null`

### `VacancyStatus`

Enum type: string.

- Values:
  - `draft`
  - `open`
  - `archived`
  - `closed`

### `VacancySummary`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `country`, `city`, `company`,
`title`, `submissionType`, `specialization`, `salaryMin`, `salaryMax`,
`salaryCurrency`, `workFormat`, `employmentType`, `status`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `country` (required): `CountryResponse`
  - `city` (required): `CityResponse | null`
  - `company` (required): `CompanySummary`
  - `title` (required): `string`
  - `submissionType` (required): `SubmissionType`
  - `specialization` (required): `Specialization`
  - `salaryMin` (required): `integer | null`
  - `salaryMax` (required): `integer | null`
  - `salaryCurrency` (required): `SalaryCurrency | null`
  - `yearsOfExperienceMin` (optional): `number | null`
  - `workFormat` (required): `WorkFormat`
  - `employmentType` (required): `EmploymentType`
  - `status` (required): `VacancyStatus`
  - `isSaved` (optional): `boolean | null`
  - `hasApplied` (optional): `boolean | null`

### `VacancyUpdateRequest`

Type: `object`.
Additional properties are not allowed.

- Fields:
  - `countryId` (optional): `string(uuid) | null`
  - `cityId` (optional): `string(uuid) | null`
  - `title` (optional): `string | null`
  - `description` (optional): `string | null`
  - `externalApplyUrl` (optional): `string(uri) | null`
  - `submissionType` (optional): `SubmissionType | null`
  - `specialization` (optional): `Specialization | null`
  - `salaryMin` (optional): `integer | null`
  - `salaryMax` (optional): `integer | null`
  - `salaryCurrency` (optional): `SalaryCurrency | null`
  - `paymentFrequency` (optional): `PaymentFrequency | null`
  - `yearsOfExperienceMin` (optional): `number | null`
  - `workFormat` (optional): `WorkFormat | null`
  - `workHoursPerWeek` (optional): `integer | null`
  - `employmentType` (optional): `EmploymentType | null`
  - `status` (optional): `VacancyStatus | null`
  - `skills` (optional): `array[VacancySkillLinkRequest] | null`

### `ValidationError`

Type: `object`.
Required fields: `loc`, `msg`, `type`.

- Fields:
  - `loc` (required): `array[string | integer]`
  - `msg` (required): `string`
  - `type` (required): `string`
  - `input` (optional): `Input`
  - `ctx` (optional): `object`

### `WorkFormat`

Enum type: string.

- Values:
  - `onsite`
  - `remote`
  - `hybrid`
