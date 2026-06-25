"""Policies — what the AI may and may not say about your company & product.

The model the product is built on: a CORPUS is the source of truth. The AI may state anything
grounded in the corpus, must CITE it, and may say nothing the corpus can't back — plus an explicit
deny-list of claims you never make. (Tone / brand-voice is a *style* choice that gates nothing, so
it is deliberately NOT a policy and does not live here.)

Sections — substance first (what may be said), then conduct (how/when):

  • Corpus      — the source documents the AI may cite. Not in the corpus → not sayable. EDITABLE.
  • Claims      — ✅ approved claims (can say, with a citation) · ⛔ forbidden claims (cannot say). EDITABLE.
  • Provability — the Gate: grounded-in-corpus + cited, deny-list honored, no fabrication.
                  PLATFORM-STANDARD, inviolable — "can't say what it can't prove" is the product.
  • Disclosure  — what a 1:1 may DO with a fact, by how you learned it (say · allude · hold). EDITABLE.
  • Anti-slop   — kills the "a bot wrote this" fingerprint. Platform defaults locked; add your own.
  • Data        — sensitive topics never referenced + whether consent is required. EDITABLE.

Editable policies persist per tenant as a DB-backed override layer (app_kv, on the volume).
Grounded in rules/<tenant>.yaml + the Gate (pipeline.personalization.creative).
"""
from __future__ import annotations

import pathlib
import re

import yaml
from fastapi import Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse

from app.server import app, templates
from pipeline.common import db
from pipeline.personalization import creative as CR

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_RULES = _ROOT / "rules" / "academy_tenant.yaml"
_CORPUS_DIR = _ROOT / "corpus"
_OVR_KEY = "policy_overrides_v1"


def _corpus_path(slug: str) -> pathlib.Path:
    safe = re.sub(r"[^a-z0-9-]", "", (slug or "").lower())
    return _CORPUS_DIR / f"{safe}.md"

RULE_PILL = {"say": "g", "allow": "g", "allude": "a", "require": "a", "hold": "r", "block": "r"}
DISCLOSURE_RULES = ["say", "allude", "hold"]
CORPUS_KINDS = ["doc", "case study", "url", "FAQ", "policy", "spec"]

SECTIONS = [
    {"key": "corpus", "label": "Corpus", "icon": "books", "editable": True,
     "blurb": "The source of truth. The AI may state anything grounded in these documents — and "
              "must cite it. Nothing the corpus can’t back is sayable. Add the documents you stand behind."},
    {"key": "claims", "label": "Claims", "icon": "seal-check", "editable": True,
     "blurb": "The explicit allow / deny list on top of the corpus: claims you’ve pre-approved (with "
              "a citation) and claims you never make about the company or product."},
    {"key": "provability", "label": "Provability", "icon": "shield-check", "editable": False,
     "blurb": "The Gate — inviolable. Every shipped line must be grounded in the corpus and cited, "
              "the deny-list is honored, and nothing unprovable gets through. This is the product."},
    {"key": "disclosure", "label": "Disclosure", "icon": "eye", "editable": True, "rules": DISCLOSURE_RULES,
     "blurb": "What a 1:1 may DO with a fact, by how you learned it — say (recite) · allude (shape it, "
              "don’t recite) · hold (never). The anti-creepiness control."},
    {"key": "antislop", "label": "Anti-slop", "icon": "broom", "editable": True,
     "blurb": "Kills the “a bot wrote this” fingerprint — AI-tells, filler words, blast-y structure. "
              "Platform defaults are locked; add your own banned phrases."},
    {"key": "data", "label": "Data & consent", "icon": "lock-key", "editable": True,
     "blurb": "Topics never referenced regardless of source, and whether consent is required before "
              "any fact is used."},
]

# ---- seeds: a FEW main, descriptive policies (a tenant edits / replaces these) ----------------
SEED_CORPUS = [
    {"name": "Product one-pager", "kind": "doc", "slug": "product-one-pager",
     "ref": "what it does + the load-bearing capabilities"},
    {"name": "Customer case studies", "kind": "case study", "slug": "customer-case-studies",
     "ref": "named outcomes & metrics you can cite"},
    {"name": "Security & compliance", "kind": "doc", "slug": "security-compliance",
     "ref": "data handling, retention, sub-processors"},
    {"name": "Pricing & packaging", "kind": "doc", "slug": "pricing-packaging",
     "ref": "tuition, plans, terms"},
]
SEED_CAN = [
    {"claim": "Every personalization ships with a receipt — source, basis, and surface policy.", "cite": "Product one-pager"},
    {"claim": "We withhold any line we can’t prove, by construction.", "cite": "Product one-pager"},
]
SEED_CANNOT = [
    "Any ROI or % we can’t cite to a case study",
    "Comparisons that name a competitor",
    "Regulatory claims not in the corpus (e.g. “FDA-approved”, “HIPAA-certified”)",
    "Roadmap / unreleased features as if shipped",
]
SEED_DISCLOSURE = [
    {"name": "First-party facts", "rule": "say",
     "desc": "They told you directly (form, reply, on-record question) — reference it by name."},
    {"name": "Involuntary signals", "rule": "allude",
     "desc": "IP, location, ad clicks, page visits — shape the message, never recite."},
    {"name": "Voice & recordings", "rule": "allude",
     "desc": "Captured calls/questions are sensitive — allude to the topic, don’t quote."},
    {"name": "Third-party & enrichment", "rule": "allude",
     "desc": "Bought or appended data targets the message, but is never quoted as if they’d told you."},
]


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


# ---- locked, platform-standard cards (grounded in the Gate) ----------------------------------
def _provability_cards() -> list[dict]:
    sup = ", ".join(list(CR._SUPERLATIVES)[:3])
    return [
        {"name": "Grounded or it doesn’t ship", "rule": "block",
         "desc": "Every claim must trace to a document in your corpus. No corpus support → the line "
                 "is blocked before it can send. The corpus is the boundary of what’s sayable."},
        {"name": "Cite the source", "rule": "require",
         "desc": "Each shipped claim carries its citation — which document backs it. That’s the receipt."},
        {"name": "Honor the deny-list", "rule": "block",
         "desc": "Anything on your Cannot-say list is blocked even if a document would support it."},
        {"name": "No fabrication", "rule": "block",
         "desc": f"Superlatives ({sup}…) and invented stats with no cited source never ship."},
        {"name": "No competitor takedowns", "rule": "block",
         "desc": "No “better/faster than X,” and never name a competitor you only inferred."},
    ]


def _antislop_cards() -> list[dict]:
    cap = CR._MSG_MAX_WORDS["cold"]
    return [
        {"name": "No AI-tell openers", "rule": "block",
         "desc": "“Hope this email finds you well,” “I wanted to reach out,” “just circling back” — "
                 "the bulk-automation fingerprint."},
        {"name": "No LLM filler words", "rule": "block",
         "desc": "delve, leverage, robust, seamless, elevate, unlock, synergy… the words that scream "
                 "“a bot wrote this.”"},
        {"name": "One ask per message", "rule": "block",
         "desc": "A single call-to-action. A second link is choice overload and reads as a blast."},
        {"name": "Short, no cold calendar link", "rule": "block",
         "desc": f"≤{cap} words on a cold first touch, and no “grab time on my calendar” before they reply."},
        {"name": "No spam-promise wording", "rule": "block",
         "desc": "“Guaranteed,” “risk-free,” “act now” — the spam-filter triggers."},
    ]


def _corpus(ovr: dict) -> list[dict]:
    items = ovr.get("corpus")
    if items is None:
        items = SEED_CORPUS
    out = []
    for i, it in enumerate(items):
        slug = it.get("slug") or _slug(it.get("name", ""))
        out.append({"id": f"c{i}", "name": it.get("name", ""), "kind": it.get("kind", "doc"),
                    "ref": it.get("ref", ""), "slug": slug, "hasfile": _corpus_path(slug).exists()})
    return out


def _can_say(ovr: dict) -> list[dict]:
    items = ovr.get("can_say")
    if items is None:
        items = SEED_CAN
    return [{"id": f"k{i}", "claim": it.get("claim", ""), "cite": it.get("cite", "")}
            for i, it in enumerate(items)]


def _cannot_say(ovr: dict) -> list[str]:
    return ovr["cannot_say"] if "cannot_say" in ovr else SEED_CANNOT


def _disclosure(ovr: dict) -> list[dict]:
    items = ovr.get("disclosure")
    if items is None:
        items = SEED_DISCLOSURE
    out = []
    for i, it in enumerate(items):
        rule = it.get("rule") if it.get("rule") in DISCLOSURE_RULES else "allude"
        out.append({"id": f"d{i}", "name": it.get("name", ""), "desc": it.get("desc", ""), "rule": rule})
    return out


def sections_view(cfg: dict, ovr: dict) -> list[dict]:
    sp = cfg.get("surface_policy") or {}
    sens = ovr["sensitive"] if "sensitive" in ovr else (sp.get("sensitive_keys") or [])
    data = {
        "corpus": {"docs": _corpus(ovr), "kinds": CORPUS_KINDS},
        "claims": {"can": _can_say(ovr), "cannot": _cannot_say(ovr)},
        "provability": {"cards": _provability_cards()},
        "disclosure": {"cards": _disclosure(ovr)},
        "antislop": {"cards": _antislop_cards(),
                     "custom": [{"raw": p} for p in (ovr.get("antislop_add") or [])]},
        "data": {"sensitive": [{"raw": k, "label": k.replace("_", " ").title()} for k in sens],
                 "consent_required": ovr.get("consent_required", bool(sp.get("consent_required")))},
    }
    return [{**s, **data.get(s["key"], {})} for s in SECTIONS]


@app.get("/policies", response_class=HTMLResponse)
def policies(request: Request):
    cfg = _load_cfg()
    ovr = _overrides()
    return templates.TemplateResponse(request, "policies.html", {
        "sections": sections_view(cfg, ovr), "rule_pill": RULE_PILL,
        "disclosure_rules": DISCLOSURE_RULES, "corpus_kinds": CORPUS_KINDS,
        "tenant": cfg.get("tenant", "—"), "dirty": bool(ovr),
    })


@app.post("/policies/save")
async def policies_save(request: Request):
    """Persist the tenant's full editable policy set (corpus + claims + disclosure + anti-slop + data)."""
    form = await request.form()

    def rows(*keys):
        cols = [form.getlist(k) for k in keys]
        return list(zip(*cols)) if cols and cols[0] else []

    corpus = [{"name": n.strip(), "kind": (k or "doc").strip(), "ref": (r or "").strip(),
               "slug": _slug(n)}
              for n, k, r in rows("c_name", "c_kind", "c_ref") if n.strip()]
    can_say = [{"claim": c.strip(), "cite": (ci or "").strip()}
               for c, ci in rows("cs_claim", "cs_cite") if c.strip()]
    cannot_say = [s.strip() for s in form.getlist("cannot") if s.strip()]
    new_cannot = form.get("cannot_new", "").strip()
    if new_cannot:
        cannot_say.append(new_cannot)
    disclosure = [{"name": n.strip(), "desc": (de or "").strip(),
                   "rule": ru if ru in DISCLOSURE_RULES else "allude"}
                  for n, de, ru in rows("d_name", "d_desc", "d_rule") if n.strip()]
    antislop = [s.strip() for s in form.getlist("antislop_add") if s.strip()]
    new_slop = form.get("antislop_new", "").strip()
    if new_slop:
        antislop.append(new_slop)
    sensitive = [s.strip() for s in form.getlist("sensitive") if s.strip()]
    _save_overrides({"corpus": corpus, "can_say": can_say, "cannot_say": cannot_say,
                     "disclosure": disclosure, "antislop_add": antislop, "sensitive": sensitive,
                     "consent_required": form.get("consent_required") == "on"})
    return RedirectResponse("/policies", status_code=303)


@app.get("/policies/corpus/{slug}", response_class=PlainTextResponse)
def policies_corpus(slug: str):
    """Serve a corpus document's content (the synthetic file the AI may cite)."""
    p = _corpus_path(slug)
    if p.exists():
        return PlainTextResponse(p.read_text())
    return PlainTextResponse("No file content yet for this document. Add a URL or upload to ground "
                             "it — the Gate cites what's here.", status_code=404)


@app.post("/policies/reset")
async def policies_reset():
    """Revert to the standard defaults (drop the tenant override layer)."""
    _clear_overrides()
    return RedirectResponse("/policies", status_code=303)
