from contextlib import asynccontextmanager
import os
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api.main import api_router
from app.api.routes import wecom_auth
from app.core.config import settings
from app.modules.data_sync.scheduler import start_scheduler, stop_scheduler
from app.modules.exam_management.scheduler import (
    start_paper_scheduler,
    stop_paper_scheduler,
)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    start_scheduler()
    start_paper_scheduler()
    yield
    stop_paper_scheduler()
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


def _resolve_wecom_verify_filename() -> str:
    configured_filename = os.getenv("WECOM_VERIFY_FILENAME")
    if configured_filename:
        return configured_filename

    verify_files = sorted(Path(__file__).parent.glob("WW_verify_*.txt"))
    if verify_files:
        return verify_files[0].name

    return "WW_verify.txt"


WECOM_VERIFY_FILENAME = _resolve_wecom_verify_filename()


@app.get(f"/{WECOM_VERIFY_FILENAME}", response_class=PlainTextResponse, tags=["wecom-verify"])
async def wecom_verify() -> str:
    verify_content = os.getenv("WECOM_VERIFY_CONTENT")
    if verify_content:
        return verify_content

    verify_path = Path(__file__).parent / WECOM_VERIFY_FILENAME
    if verify_path.exists():
        return verify_path.read_text(encoding="utf-8")

    raise HTTPException(status_code=404, detail="WeCom verify file is not configured")


def _resolve_upload_root_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    if upload_dir.is_absolute():
        return upload_dir
    project_root = Path(__file__).resolve().parents[2]
    return (project_root / upload_dir).resolve()


upload_root_dir = _resolve_upload_root_dir()
upload_root_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_root_dir)), name="uploads")
