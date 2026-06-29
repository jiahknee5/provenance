"""The FastAPI app instance + shared templates/static, imported by every route module."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pipeline.common.db import init_db
from pipeline.domain.emit import begin_request_ctx, reset_request_ctx

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

# Build/version tag shown in the sidebar foot (the "what's new" widget). Bump on each release;
# the changelog itself lives in the /help/whats-new article. Exposed to every template as globals.
APP_VERSION = "0.9"
APP_BUILT = "Jun 2026"
templates.env.globals.update(APP_VERSION=APP_VERSION, APP_BUILT=APP_BUILT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Provenance — Helix Analytics demo", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")


@app.middleware("http")
async def _scope_domain_ctx(request, call_next):
    # Give each request its own domain-emission context so concurrent visitors never share a
    # correlation_id or cross-link causation chains. anyio copies this contextvar into the
    # sync-endpoint threadpool, so emits inside the route see the request's context.
    token = begin_request_ctx(request.url.path)
    try:
        return await call_next(request)
    finally:
        reset_request_ctx(token)
