"""Policies — the Provenance Policy Standard: the provenance for what the LLMs can and cannot say.

A controlled framework a tenant company adopts and configures. Five categories, each with a
fixed rule vocabulary; every policy carries the same schema (subject · rule · scope · basis ·
enforcement). Two classes:

  • TENANT-EDITABLE  — a company configures these for itself (persisted in app_kv, DB-backed):
      Surface (say/allude/hold by how a fact was obtained) · Sensitive topics (always hold) ·
      Voice (banned phrases / tone) · Consent (required basis).
  • PLATFORM-STANDARD (inviolable) — the Gate's claim vetoes. NOT editable by design: "can't say
      what it can't prove" is the product. Shown locked, with the rule that enforces it.

Base values are grounded in real sources (rules/<tenant>.yaml, the Gate in
pipeline.personalization.creative); a tenant's edits are an override layer on top.
"""
from __future__ import annotations

import pathlib
import re

import yaml
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.server import app, templates
from pipeline.common import db
from pipeline.personalization import creative as CR

_RULES = pathlib.Path(__file__).resolve().parents[1] / "rules" / "academy_tenant.yaml"
_OVR_KEY = "policy_overrides_v1"

# ---- the standard: controlled rule vocabulary + pill colour ----------------------------------
RULE_PILL = {"say": "g", "allow": "g", "allude": "a", "require-proof": "a", "require": "a",
             "hold": "r", "block": "r", "inherit": "v"}
SURFACE_RULES = ["say", "allude", "hold"]          # what a 1:1 may do with a fact, by its source

# the five categories — the organizing standard
CATEGORIES = [
    {"key": "surface", "label": "Surface", "icon": "eye", "rules": SURFACE_RULES, "editable": True,
     "blurb": "What a 1:1 message may do with a fact, by HOW it was obtained. The anti-creepiness "
              "control. Choose say (recite) · allude (adjacent only) · hold."},
    {"key": "sensitive", "label": "Sensitive topics", "icon": "prohibit", "rules": ["hold"], "editable": True,
     "blurb": "Topics never referenced, no matter how they were learned. Add or remove your own."},
    {"key": "claim", "label": "Claims", "icon": "seal-check", "rules": ["allow", "block"], "editable": False,
     "blurb": "What kinds of claims may ship — enforced in the Gate. Platform standard, inviolable: "
              "“can’t say what it can’t prove.” Shown for transparency; locked by design."},
    {"key": "voice", "label": "Voice & hygiene", "icon": "chat-text", "rules": ["block"], "editable": True,
     "blurb": "Banned phrases / tone. Platform AI-tell defaults are locked; add your own banned phrases."},
    {"key": "consent", "label": "Consent & basis", "icon": "handshake", "rules": ["require"], "editable": True,
     "blurb": "Consent and lawful-basis requirements before any fact is used."},
]
CAT_BY = {c["key"]: c for c in CATEGORIES}

_SOURCE_LABEL = {
    "web_form": "Web form", "class_signup": "Class signup",
    "class_question_text": "In-class question · text", "class_question_voice": "In-class question · voice",
    "ad": "Ad click", "email": "Email engagement", "web_return": "Return visit",
    "rep_note": "Rep's own note", "external": "3rd-party / inferred",
}
_WHY = {
    "web_form": "they told us directly", "class_signup": "they enrolled directly",
    "class_question_text": "they asked it on the record", "class_question_voice": "voice capture is more sensitive",
    "ad": "behavioral — involuntary", "email": "behavioral — involuntary", "web_return": "behavioral — involuntary",
    "rep_note": "your inference, not their statement", "external": "inferred / 3rd-party",
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def _load_cfg() -> dict:
    try:
        return yaml.safe_load(_RULES.read_text()) or {}
    except Exception:
        return {}


# ---- tenant overrides (DB-backed; survives restarts on the persistent volume) ----------------
def _overrides() -> dict:
    db.init_db()
    conn = db.connect()
    try:
        return db.kv_get(conn, "app_kv", "k", _OVR_KEY, "v") or {}
    finally:
        conn.close()


def _save_overrides(d: dict) -> None:
    db.init_db()
    conn = db.connect()
    try:
        db.kv_put(conn, "app_kv", "k", _OVR_KEY, "v", d)
    finally:
        conn.close()


def _clear_overrides() -> None:
    db.init_db()
    conn = db.connect()
    try:
        conn.execute("DELETE FROM app_kv WHERE k=?", (_OVR_KEY,))
        conn.commit()
    finally:
        conn.close()


# ---- build the effective policy set (standard base + tenant overrides) ------------------------
def _voice_defaults() -> list[str]:
    """Platform AI-tell defaults — the locked banned phrases, drawn from the Gate."""
    return [f"“{p}”" for p in list(CR._AI_TELL_PHRASES)[:5]] + [f"word: {w}" for w in list(CR._AI_TELL_WORDS)[:6]]


def build_policies(cfg: dict, ovr: dict) -> list[dict]:
    sp = cfg.get("surface_policy") or {}
    ovr_surface = ovr.get("surface") or {}
    pol: list[dict] = []

    # Surface (editable) — base from the tenant yaml, rule overridable
    base_by = sp.get("by_source") or {}
    for src in base_by:
        rule = ovr_surface.get(src, base_by[src])
        pol.append({"cat": "surface", "id": src, "subject": _SOURCE_LABEL.get(src, src), "rule": rule,
                    "basis": _WHY.get(src, ""), "scope": "company", "editable": True,
                    "edited": src in ovr_surface and ovr_surface[src] != base_by[src]})

    # Sensitive (editable) — full effective list = override if present else yaml
    sens = ovr["sensitive"] if "sensitive" in ovr else (sp.get("sensitive_keys") or [])
    for k in sens:
        pol.append({"cat": "sensitive", "id": _slug(k), "subject": k.replace("_", " ").title(), "raw": k,
                    "rule": "hold", "basis": "sensitive category", "scope": "company", "editable": True})

    # Claims (INVIOLABLE) — the Gate's veto classes
    sup = " · ".join(list(CR._SUPERLATIVES)[:4])
    comp = " · ".join(c.strip() for c in list(CR._COMPARATIVE)[:4])
    pol += [
        {"cat": "claim", "id": "sourced", "subject": "Cited, sourced claims", "rule": "allow",
         "basis": "Gate · coverage + NLI", "scope": "all senders", "editable": False},
        {"cat": "claim", "id": "superlative", "subject": "Unprovable superlatives", "rule": "block",
         "basis": f"Gate · superlative veto ({sup})", "scope": "all senders", "editable": False},
        {"cat": "claim", "id": "numeric", "subject": "Fabricated stats / numbers", "rule": "block",
         "basis": "Gate · numeric veto", "scope": "all senders", "editable": False},
        {"cat": "claim", "id": "comparative", "subject": "Comparative / superiority", "rule": "block",
         "basis": f"Gate · comparative class ({comp})", "scope": "all senders", "editable": False},
        {"cat": "claim", "id": "competitor", "subject": "Reciting an inferred competitor", "rule": "block",
         "basis": f"Gate · allude ({len(CR.COMPETITOR_HINTS)} hints)", "scope": "all senders", "editable": False},
        {"cat": "claim", "id": "recite", "subject": "Reciting the company under allude", "rule": "block",
         "basis": "Gate · allude", "scope": "firmographic copy", "editable": False},
    ]

    # Voice (platform defaults locked + tenant additions editable)
    for d in _voice_defaults():
        pol.append({"cat": "voice", "id": _slug(d), "subject": d, "rule": "block",
                    "basis": "AI-tell · platform default", "scope": "all senders", "editable": False})
    for ph in (ovr.get("voice_add") or []):
        pol.append({"cat": "voice", "id": "add-" + _slug(ph), "subject": f"“{ph}”", "raw": ph, "rule": "block",
                    "basis": "your banned phrase", "scope": "company", "editable": True})

    # Consent (editable toggle)
    creq = ovr.get("consent_required", bool(sp.get("consent_required")))
    pol.append({"cat": "consent", "id": "consent", "subject": "Consent before personalization",
                "rule": "require" if creq else "off", "basis": "lawful basis", "scope": "company",
                "editable": True, "on": creq})
    return pol


def _grouped(cfg: dict, ovr: dict) -> list[dict]:
    pols = build_policies(cfg, ovr)
    out = []
    for cat in CATEGORIES:
        rows = [p for p in pols if p["cat"] == cat["key"]]
        out.append({**cat, "rows": rows, "editcount": sum(1 for r in rows if r.get("edited"))})
    return out


@app.get("/policies", response_class=HTMLResponse)
def policies(request: Request):
    cfg = _load_cfg()
    ovr = _overrides()
    cats = _grouped(cfg, ovr)
    n_edit = sum(1 for c in cats for r in c["rows"] if r.get("edited"))
    return templates.TemplateResponse(request, "policies.html", {
        "cats": cats, "rule_pill": RULE_PILL, "surface_rules": SURFACE_RULES,
        "tenant": cfg.get("tenant", "—"), "dirty": bool(ovr), "n_edit": n_edit,
    })


@app.post("/policies/save")
async def policies_save(request: Request):
    """Persist a tenant's edits as an override layer (DB-backed)."""
    form = await request.form()
    cfg = _load_cfg()
    base_by = (cfg.get("surface_policy") or {}).get("by_source") or {}
    surface = {}
    for k, v in form.multi_items():
        if k.startswith("surf__") and v in SURFACE_RULES:
            src = k[6:]
            if src in base_by:
                surface[src] = v
    sensitive = [s.strip() for s in form.getlist("sensitive") if s.strip()]
    voice_add = [s.strip() for s in form.getlist("voice_add") if s.strip()]
    new = form.get("voice_new", "").strip()
    if new:
        voice_add.append(new)
    ovr = {"surface": surface, "sensitive": sensitive, "voice_add": voice_add,
           "consent_required": form.get("consent_required") == "on"}
    _save_overrides(ovr)
    return RedirectResponse("/policies", status_code=303)


@app.post("/policies/reset")
async def policies_reset():
    """Revert to the standard defaults (drop the tenant override layer)."""
    _clear_overrides()
    return RedirectResponse("/policies", status_code=303)
