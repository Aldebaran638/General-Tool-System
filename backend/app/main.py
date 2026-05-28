from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api.main import api_router
from app.api.routes import wecom_auth
from app.core.config import settings
from app.modules.data_sync.scheduler import start_scheduler, stop_scheduler


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(wecom_auth.router, prefix="/api/auth")


@app.get("/WW_verify_HUz4rWBElVbwEoOX.txt", response_class=PlainTextResponse, tags=["wecom-verify"])
async def wecom_verify() -> str:
    verify_path = Path(__file__).parent / "WW_verify_HUz4rWBElVbwEoOX.txt"
    return verify_path.read_text(encoding="utf-8")


def _resolve_upload_root_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    if upload_dir.is_absolute():
        return upload_dir
    project_root = Path(__file__).resolve().parents[2]
    return (project_root / upload_dir).resolve()


upload_root_dir = _resolve_upload_root_dir()
upload_root_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_root_dir)), name="uploads")
