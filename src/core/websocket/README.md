# WebSocket

Replace the old `transport/*` layer with:

- `ConnectionRegistry`: singleton local memory store and queue owner.
- `EventBroker`: the only object handlers use to send/publish events.
- `RedisPubSubManager`: singleton Redis bridge, started once in FastAPI lifespan.
- `WebSocketConnection`: one socket lifecycle, receive loop, and send-loop.

`ConnectionRegistry.subscribe/unsubscribe` were intentionally renamed to
`join_channel/leave_channel` because Redis Pub/Sub owns subscription language;
the registry only records local channel membership.

Start Redis in FastAPI lifespan:

```py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.websocket.state import redis_pubsub_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_pubsub_manager.start()
    yield
    await redis_pubsub_manager.stop()
```
