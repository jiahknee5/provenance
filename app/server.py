"""The FastAPI app instance + shared templates/static, imported by every route module."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pipeline.common.db import init_db

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
GENERATED_DIR = ROOT / "data" / "demo" / "image_cache" / "images"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

# Build/version tag shown in the sidebar foot (the "what's new" widget). Bump on each release;
# the changelog itself lives in the /help/whats-new article. Exposed to every template as globals.
APP_VERSION = "0.9"
APP_BUILT = "Jun 2026"
templates.env.globals.update(
    APP_VERSION=APP_VERSION,
    APP_BUILT=APP_BUILT,
    static_prefix="/static",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Provenance — Helix Analytics demo", lifespan=lifespan)
app.mount("/static/generated", StaticFiles(directory=str(GENERATED_DIR)), name="generated")
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
