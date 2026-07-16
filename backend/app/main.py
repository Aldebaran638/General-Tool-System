from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api.main import api_router
from app.core.config import settings
from app.core.storage import ensure_upload_dir


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


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

# ── Storage setup (validate + mount /uploads) ─────────────────────────────────
upload_root_dir = ensure_upload_dir()
app.mount("/uploads", StaticFiles(directory=str(upload_root_dir)), name="uploads")
