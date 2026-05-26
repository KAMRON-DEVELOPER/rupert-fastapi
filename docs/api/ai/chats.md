# Chats API

Frontend API reference for the `chats` app. HTTP routes are based on the FastAPI
OpenAPI document generated from `main.py`.

## Endpoints

### Endpoint 1

- Method: `GET`
- Path: `/api/v1/chats/`
- Summary: List Chats.
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
    `PaginatedResponse_ChatListItemResponse_`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

### Endpoint 2

- Method: `GET`
- Path: `/api/v1/chats/{chat_id}/messages`
- Summary: List Chat Messages.
- Path parameters:
  - `chat_id` (string(uuid), required)
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
    `PaginatedResponse_ChatMessageResponse_`
  - `422`: Validation Error; `application/json` `HTTPValidationError`

## Schemas

### `AttachmentIdWithPositionRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `attachmentId`.

- Fields:
  - `attachmentId` (required): `string(uuid)`
  - `position` (optional): `integer | null`; default `null`

### `AttachmentStatus`

Enum type: string.

- Values:
  - `pending`
  - `ready`

### `AttachmentWithPositionResponse`

Type: `object`.
Required fields: `id`, `objectKey`, `originalFilename`, `status`, `mimeType`,
`label`, `group`, `sizeBytes`, `url`.

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
  - `position` (optional): `integer | null`
  - `url` (required): `string`; read-only

### `ChatListItemResponse`

Type: `object`.
Required fields: `id`, `user`, `isPinned`, `isMuted`, `isArchived`,
`unreadCount`.

- Fields:
  - `id` (required): `string(uuid)`
  - `user` (required): `ChatListUserResponse`
  - `isPinned` (required): `boolean`
  - `isMuted` (required): `boolean`
  - `isArchived` (required): `boolean`
  - `lastMessage` (optional): `ChatListLastMessageResponse | null`
  - `unreadCount` (required): `integer`; min 0.0

### `ChatListLastMessageResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `senderId`, `message`,
`chatId`, `replyId`, `seenByRecipient`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `senderId` (required): `string(uuid) | null`
  - `message` (required): `string | null`
  - `chatId` (required): `string(uuid)`
  - `replyId` (required): `string(uuid) | null`
  - `attachments` (optional): `array[AttachmentWithPositionResponse]`
  - `seenByRecipient` (required): `boolean | null`

### `ChatListUserResponse`

Type: `object`.
Required fields: `id`, `firstName`, `name`.

- Fields:
  - `id` (required): `string(uuid)`
  - `firstName` (required): `string`
  - `lastName` (optional): `string | null`
  - `avatarUrl` (optional): `string | null`
  - `name` (required): `string`; read-only

### `ChatEvent`

Enum type: string.

- Values:
  - `ping`
  - `join_chat`
  - `leave_chat`
  - `typing_start`
  - `typing_stop`
  - `create_chat`
  - `delete_chat`
  - `clear_chat`
  - `read_chat`
  - `send_message`
  - `update_message`
  - `delete_message`
  - `update_chat_settings`
  - `pong`
  - `error`
  - `chat_joined`
  - `chat_left`
  - `chat_created`
  - `chat_read`
  - `chat_cleared`
  - `chat_deleted`
  - `user_online`
  - `user_offline`
  - `message_created`
  - `message_updated`
  - `message_deleted`
  - `chat_settings_updated`

### `ChatMessageResponse`

Type: `object`.
Required fields: `id`, `createdAt`, `updatedAt`, `senderId`, `message`,
`chatId`, `replyId`.

- Fields:
  - `id` (required): `string(uuid)`
  - `createdAt` (required): `string(date-time)`
  - `updatedAt` (required): `string(date-time)`
  - `senderId` (required): `string(uuid) | null`
  - `message` (required): `string | null`
  - `chatId` (required): `string(uuid)`
  - `replyId` (required): `string(uuid) | null`
  - `attachments` (optional): `array[AttachmentWithPositionResponse]`

### `ChatRoomActionRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `chatId`.

- Fields:
  - `chatId` (required): `string(uuid)`

### `CreateChatMessageRequest`

Type: `object`.
Additional properties are not allowed.

- Fields:
  - `message` (optional): `string | null`; default `null`
  - `chatId` (optional): `string(uuid) | null`; default `null`
  - `replyId` (optional): `string(uuid) | null`; default `null`
  - `participantId` (optional): `string(uuid) | null`; default `null`
  - `attachments` (optional): `array[AttachmentIdWithPositionRequest]`

### `CreateChatSchema`

Type: `object`.
Additional properties are not allowed.
Required fields: `participantId`.

- Fields:
  - `participantId` (required): `string(uuid)`

### `HTTPValidationError`

Type: `object`.

- Fields:
  - `detail` (optional): `array[ValidationError]`

### `MessageActionRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `chatId`, `messageId`.

- Fields:
  - `chatId` (required): `string(uuid)`
  - `messageId` (required): `string(uuid)`

### `PaginatedResponse_ChatListItemResponse_`

Type: `object`.
Required fields: `data`, `total`.

- Fields:
  - `data` (required): `array[ChatListItemResponse]`
  - `total` (required): `integer`

### `PaginatedResponse_ChatMessageResponse_`

Type: `object`.
Required fields: `data`, `total`.

- Fields:
  - `data` (required): `array[ChatMessageResponse]`
  - `total` (required): `integer`

### `ReadChatRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `chatId`.

- Fields:
  - `chatId` (required): `string(uuid)`
  - `lastSeenAt` (optional): `string(date-time)`

### `ScopedChatActionRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `chatId`.

- Fields:
  - `chatId` (required): `string(uuid)`
  - `forParticipant` (optional): `boolean`; default `false`

### `UpdateChatSettingsActionRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `chatId`.

- Fields:
  - `isPinned` (optional): `boolean | null`; default `null`
  - `isMuted` (optional): `boolean | null`; default `null`
  - `isArchived` (optional): `boolean | null`; default `null`
  - `chatId` (required): `string(uuid)`

### `UpdateMessageActionRequest`

Type: `object`.
Additional properties are not allowed.
Required fields: `chatId`, `messageId`.

- Fields:
  - `message` (optional): `string | null`; default `null`
  - `attachments` (optional): `array[AttachmentIdWithPositionRequest] | null`;
    default `null`
  - `chatId` (required): `string(uuid)`
  - `messageId` (required): `string(uuid)`

### `ValidationError`

Type: `object`.
Required fields: `loc`, `msg`, `type`.

- Fields:
  - `loc` (required): `array[string | integer]`
  - `msg` (required): `string`
  - `type` (required): `string`
  - `input` (optional): `Input`
  - `ctx` (optional): `object`

## WebSocket

### WebSocket Endpoint

- Method: `WS`
- Path: `/api/v1/chats/ws`
- Authentication: uses the same cookie auth dependency as protected HTTP routes.
- Client messages are JSON objects with a `type` field plus the payload fields
  for that command.
- Server messages are JSON objects with a `type` field and camelCase payload
  keys.

### Client Commands

- `ping`: No payload. Server replies with `pong`.
- `join_chat`: `ChatRoomActionRequest`. Joins a chat channel.
- `leave_chat`: `ChatRoomActionRequest`. Leaves a chat channel.
- `typing_start`: `ChatRoomActionRequest`. Broadcasts typing start.
- `typing_stop`: `ChatRoomActionRequest`. Broadcasts typing stop.
- `create_chat`: `CreateChatSchema`. Creates or returns a direct chat.
- `send_message`: `CreateChatMessageRequest`. Sends a chat message.
- `update_message`: `UpdateMessageActionRequest`. Updates text or attachments.
- `delete_message`: `MessageActionRequest`. Deletes one message.
- `read_chat`: `ReadChatRequest`. Marks messages as seen.
- `clear_chat`: `ScopedChatActionRequest`. Clears messages.
- `delete_chat`: `ScopedChatActionRequest`. Deletes a chat.
- `update_chat_settings`: `UpdateChatSettingsActionRequest`. Updates pin, mute,
  or archive settings.

### Server Events

- `pong`: Reply to `ping`.
- `error`: `detail`; optional `statusCode`.
- `chat_joined`: `chatId`.
- `chat_left`: `chatId`.
- `chat_created`: `chatId`, `participantId`.
- `chat_read`: `chatId`, `userId`, `lastSeenAt`.
- `chat_cleared`: `chatId`, `userId`, `clearedAt`, `forParticipant`.
- `chat_deleted`: `chatId`, `userId`, optional `deletedAt`, `forParticipant`.
- `user_online`: `userId`.
- `user_offline`: `userId`, `lastOnlineAt`.
- `typing_start`: `chatId`, `userId`; sent to other chat members.
- `typing_stop`: `chatId`, `userId`; sent to other chat members.
- `message_created`: `message` as `ChatMessageResponse`.
- `message_updated`: `message` as `ChatMessageResponse`.
- `message_deleted`: `chatId`, `messageId`.
- `chat_settings_updated`: `chatId`, `isPinned`, `isMuted`, `isArchived`.

### WebSocket Validation Rules

- `send_message` requires non-empty `message` text or at least one attachment.
- `send_message` requires either `chatId` or `participantId`.
- `update_message` requires `message` or `attachments`.
- Attachment `position` values must be unique within a message.
- `update_chat_settings` requires at least one of `isPinned`, `isMuted`, or
  `isArchived`.
- `read_chat.lastSeenAt` defaults to the server time when omitted.
