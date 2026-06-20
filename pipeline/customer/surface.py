"""Surface policy — what a 1:1 rep may do with a customer fact.

The anti-creepiness control, made structural and auditable rather than left to a rep's
judgement. Every fact resolves to say / allude / hold from: consent, the source it came
from, and whether the key is sensitive. The map is **tenant config**
(rules/academy_tenant.yaml › surface_policy), so a tenant tunes its own line.

Principle: facts the customer *told us directly* are `say`; *behavioral / inferred /
voice / a rep's own notes* are `allude` (raise an adjacent topic, don't recite it back);
*sensitive or non-consented* facts are `hold`.
"""
from __future__ import annotations

import yaml

from pipeline.common.config import RULES_DIR
from pipeline.customer.schemas import SurfacePolicy

_DEFAULTS = {
    "consent_required": True,
    "by_source": {
        "web_form": "say", "class_signup": "say", "class_question_text": "say",
        "class_question_voice": "allude", "ad": "allude", "email": "allude",
        "web_return": "allude", "rep_note": "allude", "external": "allude",
    },
    "sensitive_keys": ["health", "family", "finances_personal", "religion", "politics"],
    "hold_sources": [],
}

# adjacent-topic openers for `allude` facts — never state the fact; open the door to it.
_OPENERS = {
    "interest:career_outcomes": "A lot of folks here are weighing where this takes their career — is that on your mind?",
    "concern:affordability": "We can always walk through how people make the investment work — want me to?",
    "concern:schedule": "Plenty of our students are juggling this around a full-time job — how are you thinking about the time?",
    "concern:readiness": "Some come in with a deep background, some with none — where do you feel you're starting from?",
    "interest:general": "What's the main thing you're hoping to get out of this?",
}


def load_policy(path: str | None = None) -> dict:
    p = path or (RULES_DIR / "academy_tenant.yaml")
    try:
        cfg = (yaml.safe_load(open(p)) or {}).get("surface_policy", {})
    except FileNotFoundError:
        cfg = {}
    out = dict(_DEFAULTS)
    out.update(cfg or {})
    # merge by_source over defaults rather than replace
    bs = dict(_DEFAULTS["by_source"])
    bs.update((cfg or {}).get("by_source", {}))
    out["by_source"] = bs
    return out


def decide(key: str, source: str, consent: bool, sensitive: bool = False,
           policy: dict | None = None) -> tuple[SurfacePolicy, list[str]]:
    pol = policy or load_policy()
    reasons: list[str] = []
    top_key = key.split(":")[0]
    if pol.get("consent_required", True) and not consent:
        return SurfacePolicy.HOLD, ["no consent on file → hold"]
    if sensitive or top_key in pol.get("sensitive_keys", []) or key in pol.get("sensitive_keys", []):
        return SurfacePolicy.HOLD, [f"sensitive ({key}) → hold, never surfaced"]
    if source in pol.get("hold_sources", []):
        return SurfacePolicy.HOLD, [f"source {source} is hold-only"]
    base = pol.get("by_source", {}).get(source, "allude")
    sp = SurfacePolicy(base)
    if sp == SurfacePolicy.SAY:
        reasons.append("customer stated this directly → may reference it")
    else:
        reasons.append(f"{source} is behavioral/inferred → adjacent topic only, don't recite")
    return sp, reasons


def opener(fact) -> str:
    """For an `allude` fact: the adjacent-topic opener a rep can use."""
    return _OPENERS.get(fact.key, _OPENERS["interest:general"])
