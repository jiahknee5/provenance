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
# Portal-prefixed static aliases: prod's Vercel rewrites map /<tenant>apt/static/* back to
# /static/*, but bare localhost and Railway-direct have no rewrite layer — serve the same
# trees at the prefixed paths so every mount style works everywhere (kills a whole class
# of local-only 404s: tenant logos, hero images, css).
for _prefix in ("gauntletapt", "planetapt", "skyfiapt"):
    app.mount(f"/{_prefix}/static/generated", StaticFiles(directory=str(GENERATED_DIR)),
              name=f"{_prefix}-generated")
    app.mount(f"/{_prefix}/static", StaticFiles(directory=str(APP_DIR / "static")),
              name=f"{_prefix}-static")
