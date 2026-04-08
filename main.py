from contextlib import asynccontextmanager
from logging import Filter, getLogger

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.apps.companies.routes import companies_router
from src.apps.users.routes import users_router
from src.apps.vacancies.routes import vacancies_router
from src.utils.boto3 import initialize_boto3
from src.utils.database import async_engine, initialize_db
from src.utils.exceptions import ApiException
from src.utils.logger import logger
from src.utils.redis import CacheManager, ChatCacheManager, RedisPubSubManager, create_redis
from src.utils.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning("🚀 Starting app_lifespan...")

    try:
        await initialize_db()
    except Exception as e:
        logger.exception(f"DB initialization exception, e: {e}")

    try:
        await initialize_boto3()
    except Exception as e:
        logger.exception(f"initialization exception startup, e: {e}")

    app.state.redis = create_redis()
    app.state.pubsub_manager = RedisPubSubManager(app.state.redis)
    app.state.chat_cache_manager = ChatCacheManager(app.state.redis)
    app.state.cache_manager = CacheManager(app.state.redis)

    try:
        yield
    finally:
        await app.state.redis.aclose()
        await async_engine.dispose()


app: FastAPI = FastAPI(lifespan=lifespan)


origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(router=companies_router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(router=vacancies_router, prefix="/api/v1/vacancies", tags=["vacancies"])


@app.get(path="/", tags=["root"])
async def root() -> dict:
    return {"status": "ok"}


@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exception: ApiException):
    logger.exception(f"HTTP {exception.status_code} error {request.url.path} detail: {exception.detail}")
    return JSONResponse(
        status_code=exception.status_code,
        content={"details": exception.detail},
        headers=exception.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    details = []

    for error in exception.errors():
        logger.critical(f"error: {error}")
        ctx = error.get("ctx", {})
        if "error" in ctx:
            details.append(str(ctx["error"]))
        else:
            loc = error.get("loc", [])
            msg = error.get("msg", "")
            if len(loc) > 1:
                field = str(loc[1]).capitalize()
                details.append(f"{field} {msg.lower()}")

    logger.warning(f"HTTP validation error during {request.method} {request.url.path}, details: {details}")
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"details": details})


class MetricsFilter(Filter):
    def filter(self, record):
        return "/metrics" not in record.getMessage()


getLogger("uvicorn.access").addFilter(MetricsFilter())
