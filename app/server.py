"""The FastAPI app instance + shared templates/static, imported by every route module."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pipeline.common.db import init_db

APP_DIR = Path(__file__).resolve().parent
REPO_DIR = APP_DIR.parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Provenance — Helix Analytics demo", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

# The "Apt" landing concept — mocks, pitch deck & brand sheet — served as a static
# site at /landing/ (html=True serves index.html for the directory root).
_LANDING_DIR = REPO_DIR / "landing"
if _LANDING_DIR.is_dir():
    app.mount("/landing", StaticFiles(directory=str(_LANDING_DIR), html=True), name="landing")
