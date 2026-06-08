from contextlib import asynccontextmanager
from logging import Filter, getLogger

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from scalar_fastapi import get_scalar_api_reference
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from apps.ws.router import ws_router
from src.apps.admin.routes import admin_router
from src.apps.attachments.routes import upload_router
from src.apps.chats.routes import chats_router
from src.apps.companies.routes import companies_router
from src.apps.locations.routes import locations_router
from src.apps.skills.routes import skills_router
from src.apps.stats.routes import stats_router
from src.apps.users.routes import users_router
from src.apps.vacancies.routes import vacancies_router
from src.core.boto3 import initialize_boto3
from src.core.database import engine
from src.core.exceptions import ApiException
from src.core.logger import logger
from src.core.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("🚀 Startup")

    await initialize_boto3()

    try:
        yield
    finally:
        logger.info("⚠️ Shutdown")
        await engine.dispose()


app: FastAPI = FastAPI(lifespan=lifespan)


origins = ["http://localhost:5173", "http://192.168.10.11:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.include_router(router=ws_router, prefix="/api/v1/ws", tags=["ws"])
app.include_router(router=stats_router, prefix="/api/v1/stats", tags=["stats"])
app.include_router(router=users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(
    router=upload_router, prefix="/api/v1/attachments", tags=["attachments"]
)
app.include_router(router=chats_router, prefix="/api/v1/chats", tags=["chats"])
app.include_router(
    router=companies_router, prefix="/api/v1/companies", tags=["companies"]
)
app.include_router(
    router=vacancies_router, prefix="/api/v1/vacancies", tags=["vacancies"]
)
app.include_router(
    router=skills_router, prefix="/api/v1/skills", tags=["skills"]
)
app.include_router(
    router=locations_router, prefix="/api/v1/locations", tags=["locations"]
)
app.include_router(router=admin_router, prefix="/api/v1/admin", tags=["admin"])


@app.get(path="/", tags=["root"])
async def root() -> dict:
    return {"status": "ok"}


@app.get("/docs/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url, scalar_proxy_url="https://proxy.scalar.com"
    )


@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exception: ApiException):
    logger.exception(
        f"HTTP {exception.status_code} error {request.url.path} detail: {exception.detail}"
    )
    return JSONResponse(
        status_code=exception.status_code,
        content={"details": exception.detail},
        headers=exception.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exception: RequestValidationError
):
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

    logger.warning(
        f"HTTP validation error during {request.method} {request.url.path}, details: {details}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"details": details},
    )


class MetricsFilter(Filter):
    def filter(self, record):
        return "/metrics" not in record.getMessage()


getLogger("uvicorn.access").addFilter(MetricsFilter())
