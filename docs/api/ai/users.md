# Users API

Frontend API reference for the `users` app. HTTP routes are based on the FastAPI
OpenAPI document generated from `main.py`.

## Endpoints

### Endpoint 1

- Method: `GET`
- Path: `/api/v1/users/auth/probe`
- Summary: Auth Probe.
- Description: Helpful handler to check user session validity
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `AuthProbeResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 2

- Method: `POST`
- Path: `/api/v1/users/auth/email`
- Summary: Email Auth.
- Request body (required):
  - `application/json` as `EmailAuthRequest`
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 3

- Method: `POST`
- Path: `/api/v1/users/auth/verify`
- Summary: Verify.
- Query parameters:
  - `token` (string, required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 4

- Method: `POST`
- Path: `/api/v1/users/auth/logout`
- Summary: Logout.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 5

- Method: `POST`
- Path: `/api/v1/users/{following_id}/follow`
- Summary: Follow.
- Path parameters:
  - `following_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `201`: Successful Response; `application/json` `FollowResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 6

- Method: `DELETE`
- Path: `/api/v1/users/{following_id}/follow`
- Summary: Unfollow .
- Path parameters:
  - `following_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 7

- Method: `GET`
- Path: `/api/v1/users/followers`
- Summary: List Followers.
- Query parameters:
  - `offset` (integer, optional); min 0, default 0
  - `limit` (integer, optional); min 1, max 100, default 20
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json`
    `PaginatedResponse_FollowResponse_`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 8

- Method: `GET`
- Path: `/api/v1/users/following`
- Summary: List Following.
- Query parameters:
  - `offset` (integer, optional); min 0, default 0
  - `limit` (integer, optional); min 1, max 100, default 20
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json`
    `PaginatedResponse_FollowResponse_`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 9

- Method: `GET`
- Path: `/api/v1/users/follow-requests`
- Summary: List Follow Requests.
- Query parameters:
  - `offset` (integer, optional); min 0, default 0
  - `limit` (integer, optional); min 1, max 100, default 20
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json`
    `PaginatedResponse_FollowResponse_`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 10

- Method: `PATCH`
- Path: `/api/v1/users/follow-requests/{follow_id}`
- Summary: Update Follow Request.
- Path parameters:
  - `follow_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `FollowUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `FollowResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 11

- Method: `GET`
- Path: `/api/v1/users/auth/google`
- Summary: Google Oauth.
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` not specified

### Endpoint 12

- Method: `GET`
- Path: `/api/v1/users/auth/google/callback`
- Summary: Google Oauth Callback.
- Query parameters:
  - `code` (string | null, optional)
  - `state` (string | null, optional)
  - `error` (string | null, optional)
- Cookie parameters:
  - `oauth_state` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 13

- Method: `GET`
- Path: `/api/v1/users/auth/github`
- Summary: Github Oauth.
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` not specified

### Endpoint 14

- Method: `GET`
- Path: `/api/v1/users/auth/github/callback`
- Summary: Github Oauth Callback.
- Query parameters:
  - `code` (string | null, optional)
  - `state` (string | null, optional)
  - `error` (string | null, optional)
- Cookie parameters:
  - `oauth_state` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 15

- Method: `POST`
- Path: `/api/v1/users/auth/password-setup`
- Summary: Password Setup.
- Query parameters:
  - `token` (string, required)
- Request body (required):
  - `application/json` as `PasswordSetupRequest`
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 16

- Method: `GET`
- Path: `/api/v1/users/resumes`
- Summary: List Resumes.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `array[ResumeSummary]`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 17

- Method: `POST`
- Path: `/api/v1/users/resumes`
- Summary: Create Resume.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `ResumeRequest`
- Responses:
  - `201`: Successful Response; `application/json` `ResumeResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 18

- Method: `GET`
- Path: `/api/v1/users/resumes/{resume_id}`
- Summary: Get Resume.
- Path parameters:
  - `resume_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `ResumeResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 19

- Method: `PATCH`
- Path: `/api/v1/users/resumes/{resume_id}`
- Summary: Update Resume.
- Path parameters:
  - `resume_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `ResumeUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `ResumeResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 20

- Method: `DELETE`
- Path: `/api/v1/users/resumes/{resume_id}`
- Summary: Delete Resume.
- Path parameters:
  - `resume_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 21

- Method: `POST`
- Path: `/api/v1/users/resumes/{resume_id}/skills`
- Summary: Create Resume Skill.
- Path parameters:
  - `resume_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `ResumeSkillLinkRequest`
- Responses:
  - `201`: Successful Response; `application/json` `ResumeSkillLinkResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 22

- Method: `PATCH`
- Path: `/api/v1/users/resumes/{resume_id}/skills/{skill_link_id}`
- Summary: Update Resume Skill.
- Path parameters:
  - `resume_id` (string(uuid), required)
  - `skill_link_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `ResumeSkillLinkUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `ResumeSkillLinkResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 23

- Method: `DELETE`
- Path: `/api/v1/users/resumes/{resume_id}/skills/{skill_link_id}`
- Summary: Delete Resume Skill.
- Path parameters:
  - `resume_id` (string(uuid), required)
  - `skill_link_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 24

- Method: `GET`
- Path: `/api/v1/users/sessions`
- Summary: List Sessions.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `array[SessionResponse]`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 25

- Method: `DELETE`
- Path: `/api/v1/users/sessions`
- Summary: Revoke Sessions.
- Query parameters:
  - `include_current` (boolean, optional); default `false`
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 26

- Method: `DELETE`
- Path: `/api/v1/users/sessions/{session_id}`
- Summary: Revoke Session.
- Path parameters:
  - `session_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 27

- Method: `GET`
- Path: `/api/v1/users/`
- Summary: Get User.
- Query parameters:
  - `summary` (boolean, optional); default `false`
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 28

- Method: `PATCH`
- Path: `/api/v1/users/`
- Summary: Update User.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (optional):
  - `multipart/form-data` as `Body_update_user_api_v1_users__patch`
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 29

- Method: `DELETE`
- Path: `/api/v1/users/`
- Summary: Delete User.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` not specified
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 30

- Method: `GET`
- Path: `/api/v1/users/skills`
- Summary: List User Skills.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json`
    `array[UserSkillLinkResponse]`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 31

- Method: `POST`
- Path: `/api/v1/users/skills`
- Summary: Create User Skill.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `UserSkillLinkRequest`
- Responses:
  - `201`: Successful Response; `application/json` `UserSkillLinkResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 32

- Method: `PATCH`
- Path: `/api/v1/users/skills/{skill_link_id}`
- Summary: Update User Skill.
- Path parameters:
  - `skill_link_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `UserSkillLinkUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `UserSkillLinkResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 33

- Method: `DELETE`
- Path: `/api/v1/users/skills/{skill_link_id}`
- Summary: Delete User Skill.
- Path parameters:
  - `skill_link_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 34

- Method: `GET`
- Path: `/api/v1/users/work-experiences`
- Summary: List Work Experiences.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json`
    `array[WorkExperienceResponse]`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 35

- Method: `POST`
- Path: `/api/v1/users/work-experiences`
- Summary: Create Work Experience.
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `WorkExperienceRequest`
- Responses:
  - `201`: Successful Response; `application/json` `WorkExperienceResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 36

- Method: `PATCH`
- Path: `/api/v1/users/work-experiences/{work_experience_id}`
- Summary: Update Work Experience.
- Path parameters:
  - `work_experience_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body (required):
  - `application/json` as `WorkExperienceUpdateRequest`
- Responses:
  - `200`: Successful Response; `application/json` `WorkExperienceResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 37

- Method: `DELETE`
- Path: `/api/v1/users/work-experiences/{work_experience_id}`
- Summary: Delete Work Experience.
- Path parameters:
  - `work_experience_id` (string(uuid), required)
- Cookie parameters:
  - `access_token` (string | null, optional)
  - `refresh_token` (string | null, optional)
  - `dau` (string | null, optional)
- Request body: none.
- Responses:
  - `200`: Successful Response; `application/json` `MessageResponse`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

## Schemas

### `AuthProbeResponse`

Type: `object`.
Required fields: `isAuthenticated`.

- Fields:
  - `isAuthenticated` (required): `boolean`

### `Body_update_user_api_v1_users__patch`

Type: `object`.

- Fields:
  - `avatar` (optional): `string | null`
  - `banner` (optional): `string | null`
  - `firstName` (optional): `string | null`
  - `lastName` (optional): `string | null`
  - `country_id` (optional): `string(uuid) | null`
  - `city_id` (optional): `string(uuid) | null`
  - `headline` (optional): `string | null`
  - `birthdate` (optional): `string(date) | null`
  - `bio` (optional): `string | null`
  - `specialization` (optional): `Specialization | null`
  - `phoneNumber` (optional): `string | null`
  - `githubUrl` (optional): `string | null`
  - `telegramUsername` (optional): `string | null`
  - `followPolicy` (optional): `FollowPolicy | null`
  - `jobSearchStatus` (optional): `JobSearchStatus | null`
  - `deleteAvatar` (optional): `boolean | null`
  - `deleteBanner` (optional): `boolean | null`

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

### `EmailAuthRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `email`, `password`.

- Fields:
  - `email` (required): `string(email)`
  - `password` (required): `string`
  - `firstName` (optional): `string | null`
  - `lastName` (optional): `string | null`

### `EmploymentType`

Enum type: string.

- Values:
  - `full_time`
  - `part_time`
  - `contract`
  - `internship`

### `FollowPolicy`

Enum type: string.

- Values:
  - `auto_accept`
  - `require_approval`

### `FollowResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `followerId`, `followingId`,
`status`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `followerId` (required): `string(uuid)`
  - `followingId` (required): `string(uuid)`
  - `status` (required): `FollowStatus`
  - `follower` (optional): `FollowUserResponse | null`
  - `following` (optional): `FollowUserResponse | null`

### `FollowStatus`

Enum type: string.

- Values:
  - `pending`
  - `accepted`
  - `declined`

### `FollowUpdateRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `status`.

- Fields:
  - `status` (required): `FollowStatus`

### `FollowUserResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `firstName`, `lastName`,
`headline`, `avatarUrl`, `specialization`, `followPolicy`, `jobSearchStatus`,
`followersCount`, `followingsCount`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `firstName` (required): `string`
  - `lastName` (required): `string | null`
  - `headline` (required): `string | null`
  - `avatarUrl` (required): `string | null`
  - `specialization` (required): `Specialization | null`
  - `followPolicy` (required): `FollowPolicy`
  - `jobSearchStatus` (required): `JobSearchStatus`
  - `followersCount` (required): `integer`
  - `followingsCount` (required): `integer`

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

### `PaginatedResponse_FollowResponse_`

Type: `object`.
Required fields: `data`, `total`.

- Fields:
  - `data` (required): `array[FollowResponse]`
  - `total` (required): `integer`

### `PasswordSetupRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `password`.

- Fields:
  - `password` (required): `string`

### `ProficiencyLevel`

Enum type: string.

- Values:
  - `beginner`
  - `intermediate`
  - `advanced`
  - `expert`

### `ResumeRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `countryId`, `title`, `specialization`.

- Fields:
  - `countryId` (required): `string(uuid)`
  - `cityId` (optional): `string(uuid) | null`
  - `title` (required): `string`; max length 128
  - `summary` (optional): `string | null`
  - `specialization` (required): `Specialization`
  - `salaryExpectationMin` (optional): `integer | null`
  - `salaryExpectationMax` (optional): `integer | null`
  - `salaryCurrency` (optional): `SalaryCurrency | null`
  - `workFormat` (optional): `WorkFormat | null`
  - `employmentType` (optional): `EmploymentType | null`
  - `skills` (optional): `array[ResumeSkillLinkRequest]`

### `ResumeResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `country`, `city`, `userId`,
`title`, `summary`, `specialization`, `salaryExpectationMin`,
`salaryExpectationMax`, `salaryCurrency`, `workFormat`, `employmentType`,
`skills`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `country` (required): `CountryResponse`
  - `city` (required): `CityResponse | null`
  - `userId` (required): `string(uuid)`
  - `title` (required): `string`
  - `summary` (required): `string | null`
  - `specialization` (required): `Specialization`
  - `salaryExpectationMin` (required): `integer | null`
  - `salaryExpectationMax` (required): `integer | null`
  - `salaryCurrency` (required): `SalaryCurrency | null`
  - `workFormat` (required): `WorkFormat | null`
  - `employmentType` (required): `EmploymentType | null`
  - `skills` (required): `array[ResumeSkillLinkResponse]`

### `ResumeSkillLinkRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `skillId`, `proficiency`.

- Fields:
  - `skillId` (required): `string(uuid)`
  - `proficiency` (required): `ProficiencyLevel`
  - `lastUsedAt` (optional): `string(date) | null`

### `ResumeSkillLinkResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `resumeId`, `skill`,
`proficiency`, `lastUsedAt`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `resumeId` (required): `string(uuid)`
  - `skill` (required): `SkillResponse`
  - `proficiency` (required): `ProficiencyLevel`
  - `lastUsedAt` (required): `string(date) | null`

### `ResumeSkillLinkUpdateRequest`

Type: `object`.
Additional properties are not allowed.

- Fields:
  - `proficiency` (optional): `ProficiencyLevel | null`
  - `lastUsedAt` (optional): `string(date) | null`

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

### `ResumeUpdateRequest`

Type: `object`.
Additional properties are not allowed.

- Fields:
  - `countryId` (optional): `string(uuid) | null`
  - `cityId` (optional): `string(uuid) | null`
  - `title` (optional): `string | null`
  - `summary` (optional): `string | null`
  - `specialization` (optional): `Specialization | null`
  - `salaryExpectationMin` (optional): `integer | null`
  - `salaryExpectationMax` (optional): `integer | null`
  - `salaryCurrency` (optional): `SalaryCurrency | null`
  - `workFormat` (optional): `WorkFormat | null`
  - `employmentType` (optional): `EmploymentType | null`
  - `skills` (optional): `array[ResumeSkillLinkRequest] | null`

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

### `SessionResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `userId`, `userAgent`,
`ipAddr`, `deviceName`, `isActive`, `lastActivityAt`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `userId` (required): `string(uuid)`
  - `userAgent` (required): `string | null`
  - `ipAddr` (required): `string | null`
  - `deviceName` (required): `string | null`
  - `isActive` (required): `boolean`
  - `lastActivityAt` (required): `string(date-time)`

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

### `UserSkillLinkRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `skillId`, `proficiency`.

- Fields:
  - `skillId` (required): `string(uuid)`
  - `proficiency` (required): `ProficiencyLevel`
  - `lastUsedAt` (optional): `string(date) | null`

### `UserSkillLinkResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `skill`, `proficiency`,
`lastUsedAt`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `skill` (required): `SkillResponse`
  - `proficiency` (required): `ProficiencyLevel`
  - `lastUsedAt` (required): `string(date) | null`

### `UserSkillLinkUpdateRequest`

Type: `object`.
Additional properties are not allowed.

- Fields:
  - `proficiency` (optional): `ProficiencyLevel | null`
  - `lastUsedAt` (optional): `string(date) | null`

### `ValidationError`

Type: `object`.
Required fields: `loc`, `msg`, `type`.

- Fields:
  - `loc` (required): `array[string | integer]`
  - `msg` (required): `string`
  - `type` (required): `string`
  - `input` (optional): `Input`
  - `ctx` (optional): `object`

### `WorkExperienceRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `companyName`, `position`, `startedAt`.

- Fields:
  - `companyName` (required): `string`; max length 128
  - `location` (optional): `string | null`
  - `position` (required): `string`; max length 128
  - `description` (optional): `string | null`
  - `startedAt` (required): `string(date)`
  - `endedAt` (optional): `string(date) | null`

### `WorkExperienceResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `userId`, `companyName`,
`location`, `position`, `description`, `startedAt`, `endedAt`, `isCurrent`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `userId` (required): `string(uuid)`
  - `companyName` (required): `string`
  - `location` (required): `string | null`
  - `position` (required): `string`
  - `description` (required): `string | null`
  - `startedAt` (required): `string(date)`
  - `endedAt` (required): `string(date) | null`
  - `isCurrent` (required): `boolean`; read-only

### `WorkExperienceUpdateRequest`

Type: `object`.
Additional properties are not allowed.

- Fields:
  - `companyName` (optional): `string | null`
  - `location` (optional): `string | null`
  - `position` (optional): `string | null`
  - `description` (optional): `string | null`
  - `startedAt` (optional): `string(date) | null`
  - `endedAt` (optional): `string(date) | null`

### `WorkFormat`

Enum type: string.

- Values:
  - `onsite`
  - `remote`
  - `hybrid`
