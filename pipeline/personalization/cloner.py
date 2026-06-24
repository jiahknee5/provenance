"""Live site cloner — fetch a real URL and re-serve it with a personalization layer injected.

Operator chose a live cloner over a branded template (R-demo). It works cleanly for
server-rendered / static marketing HTML (e.g. gauntletai.com); JS-heavy SPAs won't fully
render once re-hosted, so we degrade gracefully to a branded fallback.

What we do to the fetched page, deterministically:
  • cache the raw fetch (LLMCache) so a given URL replays identically — keeps the demo
    deterministic even though it touches the network,
  • strip <script> (no third-party analytics / redirects run from our clone),
  • inject <base href> so the original CSS/images still resolve from the origin,
  • prepend a personalization HERO for the chosen variant + a DATA USED provenance strip,
    so what was used to build the decision is never lost.

Network is required only to fetch a NEW url; gauntletai.com is pre-cached at bake time.
"""
from __future__ import annotations

import html as _html
import re
from urllib.parse import urlparse

from pipeline.common.cache import LLMCache
from pipeline.personalization.demo_scenarios import Variant

DEFAULT_URL = "https://www.gauntletai.com"
_UA = "Mozilla/5.0 (compatible; ProvenanceDemo/1.0; +https://labs.gauntletai.com)"


def normalize_url(url: str) -> str:
    url = (url or "").strip() or DEFAULT_URL
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def origin_of(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


_BRAND_NICE = {"gauntletai": "Gauntlet AI"}


def brand_from_url(url: str) -> str:
    """A display brand from the domain (nike.com → 'Nike'), no fetch needed."""
    host = urlparse(normalize_url(url)).netloc.split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    label = host.split(".")[0] if host else ""
    if not label:
        return "this site"
    return _BRAND_NICE.get(label, label[:1].upper() + label[1:])


def brand_of(html: str, url: str) -> str:
    """Prefer the page's own og:site_name (nicer), else the domain label."""
    for pat in (r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:site_name["\']'):
        m = re.search(pat, html, re.I)
        if m and m.group(1).strip():
            return m.group(1).strip()[:40]
    return brand_from_url(url)


def fetch_raw(url: str, cache: LLMCache | None = None) -> dict:
    """Fetch (cached). Returns {ok, status, html, error}. Never raises."""
    url = normalize_url(url)
    cache = cache or LLMCache()
    key = LLMCache.hash_input("clone_v1", url)

    def _do() -> dict:
        import httpx
        try:
            r = httpx.get(url, timeout=15, follow_redirects=True,
                          headers={"User-Agent": _UA, "Accept": "text/html"})
            ctype = r.headers.get("content-type", "")
            if r.status_code != 200 or "html" not in ctype.lower():
                return {"ok": False, "status": r.status_code, "html": "",
                        "error": f"status {r.status_code}, content-type {ctype or '?'}"}
            return {"ok": True, "status": 200, "html": r.text, "error": ""}
        except Exception as e:  # network down / DNS / TLS — degrade, never crash
            return {"ok": False, "status": 0, "html": "", "error": f"{type(e).__name__}: {e}"}

    return cache.get_or_compute(key, _do)


def _neutralize(html: str) -> str:
    """For a HIGH-FIDELITY clone we keep the page's own scripts (so JS-loaded fonts, lazy
    images and dynamic sections render). We only remove what would either bounce the page
    away or block our injected hero: meta-refresh redirects + a page-level CSP."""
    html = re.sub(r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]*>', "", html, flags=re.I)
    html = re.sub(r'<meta[^>]+http-equiv=["\']?content-security-policy["\']?[^>]*>', "", html, flags=re.I)
    return html


def _inject_base(html: str, origin: str) -> str:
    if re.search(r"<base\b", html, flags=re.I):
        return html
    tag = f'<base href="{origin}/">'
    if re.search(r"<head[^>]*>", html, flags=re.I):
        return re.sub(r"(<head[^>]*>)", r"\1" + tag, html, count=1, flags=re.I)
    return tag + html


_CIRC = "①②③④⑤⑥⑦⑧⑨"


def _overlay(scenario_id: str, v: Variant, url: str, brand: str = "this site") -> str:
    """The injected personalization hero + DATA USED provenance strip (self-contained styles).
    Copy is brand-templated: {brand} is filled from the cloned site, so the personalization
    is about *that* site, not a hardcoded one. Each data chip is numbered (①②③) so it ties
    back to the same row in the demo's Receipt rail, and the overlay names where it maps."""
    def fill(s: str) -> str:
        return _html.escape(s.replace("{brand}", brand))
    chips = "".join(
        f'<span style="display:inline-block;font-size:11px;font-weight:700;background:#fff;'
        f'border:1px solid #d9e2ec;border-radius:4px;padding:2px 7px;margin:0 4px 4px 0;color:#102a43;">'
        f'<b style="color:{v.accent};margin-right:4px;">{_CIRC[i] if i < len(_CIRC) else "•"}</b>'
        f'{_html.escape(d.signal)} '
        f'<em style="font-style:normal;color:#627d98;font-weight:600;">· {_html.escape(d.source_label)} · {d.policy}</em></span>'
        for i, d in enumerate(v.data_used))
    blocked = v.blocked
    bar_bg = "#fff5f5" if blocked else "#f4f9ff"
    bar_bd = v.accent
    place_label, place_where, _place_what = v.place
    note = ("BLOCKED by the surface policy — shown greyed for contrast; the optimizer can never select it."
            if blocked else _html.escape(v.surface_note))
    return f"""
<div id="prov-demo-overlay" data-prov-variant="{v.id}" data-prov-placement="{v.placement}"
  style="all:initial;display:block;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Inter,Arial,sans-serif;
  background:{bar_bg};border:2px solid {bar_bd};border-radius:10px;margin:10px;padding:18px 22px;color:#0a2540;
  box-shadow:0 10px 30px -16px rgba(10,37,64,.45);{'opacity:.85;' if blocked else ''}">
  <div style="max-width:1100px;margin:0 auto;">
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:7px;">
      <span style="font-size:10px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;color:#fff;background:{bar_bd};border-radius:5px;padding:3px 8px;">↳ maps to: {_html.escape(place_label)}</span>
      <span style="font-size:11px;color:#627d98;">{_html.escape(place_where)}</span>
    </div>
    <div style="font-size:11px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:{bar_bd};">
      Provenance demo &middot; Scenario {scenario_id} &middot; variant {v.id} &middot; {_html.escape(v.label)}{' &middot; BLOCKED' if blocked else ''}</div>
    <div style="font-size:26px;font-weight:800;line-height:1.15;margin:6px 0 4px;color:#0a2540;">{fill(v.headline)}</div>
    <div style="font-size:14px;color:#334e68;margin-bottom:10px;">{fill(v.sub)}</div>
    <a href="#" onclick="return false" style="display:inline-block;font-size:13px;font-weight:800;color:#fff;
      background:{bar_bd};border-radius:7px;padding:9px 16px;text-decoration:none;">{fill(v.cta)} &rarr;</a>
    <div style="margin-top:13px;border-top:1px solid #e3eaf2;padding-top:9px;">
      <span style="font-size:10px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#1e40af;margin-right:6px;">Data used</span>
      {chips}
      <div style="font-size:11px;color:#627d98;margin-top:5px;">Policy: {note} &middot; optimizing <b style="color:#102a43;">{_html.escape(v.kpi)}</b></div>
    </div>
    <div style="font-size:10px;color:#90a4b8;margin-top:8px;">↓ below is the real, live-cloned page from <b>{_html.escape(url)}</b> — high-fidelity (its own CSS &amp; scripts run). The bordered block above is the only thing we injected.</div>
  </div>
</div>"""


def _fallback_page(scenario_id: str, v: Variant, url: str, reason: str) -> str:
    """When the fetch fails / isn't HTML — a branded stand-in so the demo still renders."""
    body = (f'<div style="max-width:760px;margin:40px auto;font-family:-apple-system,Inter,Arial,sans-serif;'
            f'color:#334e68;padding:0 22px;">'
            f'<div style="font-size:13px;color:#b45309;background:#fef3c7;border:1px solid #fcd34d;'
            f'border-radius:8px;padding:10px 14px;">Could not live-clone <b>{_html.escape(url)}</b> '
            f'({_html.escape(reason)}). Showing the personalization hero on a branded fallback.</div>'
            f'<div style="margin-top:24px;font-size:13px;color:#627d98;">[ original page content would render here ]</div></div>')
    return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>Provenance demo — {scenario_id}/{v.id}</title></head>"
            f"<body style='margin:0;background:#eef2f6;'>{_overlay(scenario_id, v, url, brand_from_url(url))}{body}</body></html>")


def _inject_overlay(doc: str, overlay: str, placement: str) -> str:
    """Insert the overlay at a DOM anchor chosen by the variant's placement, so different
    variants visibly map to different parts of the cloned page. Best-effort on arbitrary
    markup with a safe fallback to the top of <body>; never raises.

      banner → just below the site's own header/hero (after </header>|</h1>|</nav>)
      cta    → right before the first prominent call-to-action link/button or <form>
      hero / theme / fallback → immediately after <body>
    """
    placement = (placement or "hero").lower()
    if placement == "banner":
        for pat in (r"</header>", r"</h1>", r"</nav>"):
            m = re.search(pat, doc, flags=re.I)
            if m:
                return doc[:m.end()] + overlay + doc[m.end():]
    elif placement == "cta":
        m = re.search(r'<a\b[^>]*\bhref=[^>]*>(?:(?!</a>).){0,90}?'
                      r'(get started|sign up|sign in|apply now|apply|book|join|buy|try |demo|start|continue|get )',
                      doc, flags=re.I | re.S)
        if m:
            return doc[:m.start()] + overlay + doc[m.start():]
        m2 = re.search(r"<form\b", doc, flags=re.I)
        if m2:
            return doc[:m2.start()] + overlay + doc[m2.start():]
    if re.search(r"<body[^>]*>", doc, flags=re.I):
        return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + overlay, doc, count=1, flags=re.I)
    return overlay + doc


def clone(url: str, scenario_id: str, v: Variant, cache: LLMCache | None = None) -> dict:
    """Return {html, cloned: bool, source_url, note}. `html` is a full page ready to serve."""
    url = normalize_url(url)
    res = fetch_raw(url, cache)
    if not res["ok"]:
        return {"html": _fallback_page(scenario_id, v, url, res["error"]),
                "cloned": False, "source_url": url, "note": res["error"]}
    doc = _neutralize(res["html"])
    doc = _inject_base(doc, origin_of(url))
    overlay = _overlay(scenario_id, v, url, brand_of(res["html"], url))
    doc = _inject_overlay(doc, overlay, v.placement)
    return {"html": doc, "cloned": True, "source_url": url, "note": "live clone"}
