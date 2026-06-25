"""Policies surface — the provenance for what the LLMs can and cannot say.

Three scopes, each a layer the Gate enforces, most-general first:
  • Company  — tenant-wide surface policy (say / allude / hold by HOW a fact was obtained) +
               always-held sensitive topics + consent. Source of truth: rules/<tenant>.yaml.
  • Product  — the claim-class rules the Gate runs on every generated line (no unprovable
               superlatives, no fabricated numbers, no comparative / competitor claims).
  • Personal — per-sender rules: say only what they told you; allude to involuntary signals;
               a sender inherits Company + Product policy and may tighten, never loosen.

Nothing here is hand-waved: the Company rows are read from the tenant YAML and the Product rows
name the actual Gate lenses in pipeline.personalization.creative / pipeline.gate.
"""
from __future__ import annotations

import pathlib

import yaml
from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.personalization import creative as CR

_RULES = pathlib.Path(__file__).resolve().parents[1] / "rules" / "academy_tenant.yaml"

# rule → quiet.css pill variant + display order (say first, hold/block last)
RULE_PILL = {"say": "g", "allow": "g", "allude": "a", "hold": "r", "block": "r",
             "inherit": "v", "consent": "b"}
_RANK = {"say": 0, "allow": 0, "allude": 1, "inherit": 2, "consent": 2, "hold": 3, "block": 3}

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


def _load() -> dict:
    try:
        return yaml.safe_load(_RULES.read_text()) or {}
    except Exception:
        return {}


def _company_rows(cfg: dict) -> list[dict]:
    sp = cfg.get("surface_policy") or {}
    rows: list[dict] = []
    if sp.get("consent_required"):
        rows.append({"topic": "Consent", "rule": "consent",
                     "detail": "Personalization is gated on consent before any fact is used.",
                     "basis": "consent_required: true", "scope": "all reps · all messages"})
    for src, rule in (sp.get("by_source") or {}).items():
        rows.append({"topic": _SOURCE_LABEL.get(src, src), "rule": rule,
                     "detail": ("Reference it directly in a 1:1 message." if rule == "say"
                                else "Touch the adjacent topic only — never recite the fact."),
                     "basis": _WHY.get(src, ""), "scope": "all reps · all messages"})
    for k in (sp.get("sensitive_keys") or []):
        rows.append({"topic": k.replace("_", " ").title(), "rule": "hold",
                     "detail": "Never referenced, no matter how we learned it.",
                     "basis": "sensitive category", "scope": "all reps · all messages"})
    rows.sort(key=lambda r: _RANK.get(r["rule"], 9))
    return rows


def _product_rows() -> list[dict]:
    sup = " · ".join(list(CR._SUPERLATIVES)[:4])
    comp = " · ".join(c.strip() for c in list(CR._COMPARATIVE)[:4])
    return [
        {"topic": "Cited, sourced claims", "rule": "say",
         "detail": "Any line whose every claim traces to a source in the library.",
         "basis": "Gate · coverage + NLI", "scope": "every generated line"},
        {"topic": "Only verified variants ship", "rule": "allow",
         "detail": "The optimizer can only promote a variant whose lines already cleared the Gate.",
         "basis": "Optimizer × Gate", "scope": "every experiment"},
        {"topic": "Unprovable superlatives", "rule": "block",
         "detail": f"#1 / best / leading / guaranteed … ({sup}).",
         "basis": "Gate · superlative veto", "scope": "every generated line"},
        {"topic": "Fabricated stats / numbers", "rule": "block",
         "detail": "A % / $ / ×N not present in the cited sources.",
         "basis": "Gate · numeric veto", "scope": "every generated line"},
        {"topic": "Comparative / superiority claims", "rule": "block",
         "detail": f"“{comp}” … blocked unless backed by a proof.",
         "basis": "Gate · comparative class", "scope": "Tier-3 competitive copy"},
        {"topic": "Reciting an inferred competitor", "rule": "block",
         "detail": f"Naming a competitor we only inferred ({len(CR.COMPETITOR_HINTS)} distinctive hints).",
         "basis": "Gate · allude", "scope": "Tier-3 competitive copy"},
        {"topic": "Reciting the company under allude", "rule": "block",
         "detail": "Naming the visitor's company resolved from their IP.",
         "basis": "Gate · allude", "scope": "firmographic copy"},
    ]


def _personal_rows() -> list[dict]:
    return [
        {"topic": "Facts they told you directly", "rule": "say",
         "detail": "Form / signup / on-record questions — reference them.",
         "basis": "first-party", "scope": "this sender"},
        {"topic": "Involuntary signals", "rule": "allude",
         "detail": "IP / location / behavior — shape the message, never recite.",
         "basis": "involuntary", "scope": "this sender"},
        {"topic": "Your own notes", "rule": "allude",
         "detail": "Don't quote your rep notes back at them (rep_note).",
         "basis": "your inference", "scope": "this sender"},
        {"topic": "Inherits Company + Product policy", "rule": "inherit",
         "detail": "A sender may tighten any rule, never loosen one.",
         "basis": "policy composition", "scope": "this sender"},
    ]


@app.get("/policies", response_class=HTMLResponse)
def policies(request: Request):
    cfg = _load()
    officers = cfg.get("admissions_officers") or []
    tabs = [
        {"key": "company", "label": "Company", "icon": "buildings",
         "blurb": "Tenant-wide surface policy — what a 1:1 message may do with a fact, by how we obtained it. "
                  "Read from the tenant config; the Gate enforces it.",
         "rows": _company_rows(cfg), "meta": f"tenant: {cfg.get('tenant', '—')} · rules/academy_tenant.yaml"},
        {"key": "product", "label": "Product", "icon": "package",
         "blurb": "The claim-class rules the Gate runs on every generated line. Deterministic vetoes — "
                  "a blocked line never becomes a sendable variant.",
         "rows": _product_rows(), "meta": "pipeline.gate · pipeline.personalization.creative"},
        {"key": "personal", "label": "Personal", "icon": "user",
         "blurb": "Per-sender rules. A sender says only what the recipient told them, alludes to everything "
                  "involuntary, and inherits the layers above — they can tighten, never loosen.",
         "rows": _personal_rows(),
         "meta": ("senders: " + ", ".join(o.get("name", "?") for o in officers)) if officers else "per-sender"},
    ]
    return templates.TemplateResponse(request, "policies.html", {"tabs": tabs, "rule_pill": RULE_PILL})
