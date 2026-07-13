"""Static UI design mockups for demo navigation pages.

  GET /apt/mockups           — gallery index (links to all 15 variants)
  GET /apt/mockups/{name}    — serve sitemap-a, hub-b, direct-c, etc.
  GET /apt/mockups/curavive        — CuraVive replica direction gallery (5 mockups)
  GET /apt/mockups/curavive/{v}    — serve one CuraVive mockup (a–e)
"""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from app.server import app

_MOCKUP_DIR = Path(__file__).resolve().parent / "static" / "mockups" / "demo-nav"
_CURAVIVE_DIR = Path(__file__).resolve().parent / "static" / "mockups" / "curavive"
_CURAVIVE_VARIANTS = {"a", "b", "c", "d", "e"}

_PAGES: tuple[tuple[str, str], ...] = (
    ("sitemap", "Demo sitemap"),
    ("hub", "Ops hub"),
    ("direct", "Direct gallery"),
    ("email", "Email gallery"),
    ("ads", "Ads grid"),
)
_VARIANTS: tuple[tuple[str, str], ...] = (
    ("a", "Campaign command center"),
    ("b", "Product tour"),
    ("c", "Sales deck"),
)
_ALLOWED = {f"{page}-{var}" for page, _ in _PAGES for var, _ in _VARIANTS}


def _mockup_path(name: str) -> Path:
    stem = name.removesuffix(".html")
    if stem not in _ALLOWED or ".." in stem or "/" in stem:
        raise HTTPException(status_code=404, detail="mockup not found")
    path = _MOCKUP_DIR / f"{stem}.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="mockup not found")
    return path


@app.get("/apt/mockups", response_class=HTMLResponse)
def mockups_index() -> FileResponse:
    index = _MOCKUP_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="mockup index missing")
    return FileResponse(index, media_type="text/html")


@app.get("/apt/mockups/curavive", response_class=HTMLResponse)
def curavive_mockups_index() -> FileResponse:
    index = _CURAVIVE_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="curavive gallery missing")
    return FileResponse(index, media_type="text/html")


@app.get("/apt/mockups/curavive/{variant}", response_class=HTMLResponse)
def curavive_mockup(variant: str) -> FileResponse:
    v = variant.removesuffix(".html")
    if v not in _CURAVIVE_VARIANTS:
        raise HTTPException(status_code=404, detail="mockup not found")
    path = _CURAVIVE_DIR / f"{v}.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="mockup not found")
    return FileResponse(path, media_type="text/html")


@app.get("/apt/mockups/{name}", response_class=HTMLResponse)
def mockup_page(name: str) -> FileResponse:
    return FileResponse(_mockup_path(name), media_type="text/html")
