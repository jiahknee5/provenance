"""Render a personalized page from the signal catalog, at a tier × mode.

Two modes, one catalog — this is the whole point of the demo:

  TASTEFUL  honours each signal's surface policy (the funnel's anti-creepiness control):
            `say`    facts are stated literally,
            `allude` facts only *steer* tone/selection — never recited,
            `hold`   facts are known but never used.

  CREEPY    switches the policy off. Every signal available at this tier is printed verbatim,
            each tagged with exactly where it came from. Nothing new is collected — it's the
            *same* data; the only thing removed is the restraint.

The contrast (a short, warm tasteful page vs. a wall of provenance-tagged surveillance) is
the lesson: "creepy" isn't more data, it's the absence of a surface policy.
"""
from __future__ import annotations

from pipeline.customer.schemas import SurfacePolicy
from pipeline.personalization import signals as S
from pipeline.personalization.signals import Signal

# Dispositions — what we did with a signal, for the ledger's right-hand column.
SAID = "said"            # stated literally in the copy
STEER = "steer"          # used to shape tone/selection, not stated
WITHHELD = "withheld"    # available but held back (surface=hold, tasteful)
SHOWN = "shown"          # printed verbatim (creepy mode)
LOCKED = "locked"        # not available at this tier


def _val(sid: str) -> str:
    return S.CATALOG_BY_ID[sid].value


# --------------------------------------------------------------------------- #
# Tasteful copy — built only from `say` facts (literal) + `allude` facts (steer).
# Hand-authored so it reads like a real, restrained, human landing page.
# --------------------------------------------------------------------------- #
def _tasteful_copy(avail_ids: set[str]) -> dict:
    """Return {headline, lines:[{text, from:[signal_ids], policy}], steer_note}."""
    say = lambda sid: sid in avail_ids and S.CATALOG_BY_ID[sid].surface == SurfacePolicy.SAY
    has = lambda sid: sid in avail_ids

    lines: list[dict] = []

    # Greeting — strongest `say` identity available, else a neutral, location-only hello.
    if say("g_profile"):
        headline = "Welcome back, Maya."
        lines.append({"text": "Good to see you again.", "from": ["g_profile"], "policy": "say"})
    elif say("d_name"):
        headline = "Hi Maya."
        lines.append({"text": "Thanks for being in touch.", "from": ["d_name"], "policy": "say"})
    elif has("ip_city"):
        headline = "Build a career in AI — nights and weekends."
        lines.append({"text": "Live classes that fit around a full-time job.",
                      "from": [], "policy": "—"})
    else:
        headline = "Build a career in AI — nights and weekends."
        lines.append({"text": "Live, instructor-led classes.", "from": [], "policy": "—"})

    # `say`: the customer told us their goal → we may quote it back.
    if say("d_goal"):
        lines.append({"text": "You said you want to switch into AI without going broke — "
                              "that's exactly who the night cohort is built for.",
                      "from": ["d_goal"], "policy": "say"})

    # `say`: existing relationship → reference it warmly.
    if say("c_customer"):
        lines.append({"text": "You took Intro to Python with us in 2023 — this is the natural next step.",
                      "from": ["c_customer"], "policy": "say"})

    # `allude`: behavioral interest STEERS what we feature — we never recite the behavior.
    steer_sources = [sid for sid in ("pages", "dwell", "abandoned", "visits")
                     if has(sid) and S.CATALOG_BY_ID[sid].surface == SurfacePolicy.ALLUDE]
    if steer_sources:
        lines.append({"text": "Here's the night cohort, with the financing options up front.",
                      "from": steer_sources, "policy": "allude (steer)"})

    # `allude`: schedule/affordability inferred → adjacent benefit, phrased generally.
    if has("ip_city") or has("isp"):
        lines.append({"text": "Classes run after work, from home — no commute.",
                      "from": [s for s in ("isp", "localtime") if has(s)], "policy": "allude (steer)"})

    lines.append({"text": "→ See the next night cohort", "from": [], "policy": "cta"})

    steer_note = ("We *know* far more (see the ledger) — schedule pressure, comparison shopping, "
                  "a new baby, income. A surface policy keeps it out of the copy: we let it quietly "
                  "shape what we feature, but we don't say it.")
    return {"headline": headline, "lines": lines, "steer_note": steer_note}


# --------------------------------------------------------------------------- #
# Creepy copy — every available signal, verbatim, provenance-tagged.
# --------------------------------------------------------------------------- #
def _creepy_copy(avail: list[Signal]) -> dict:
    headline = "We've been expecting you, Maya. 👁"
    blocks: list[dict] = []
    for t in S.TIERS:
        rows = [s for s in avail if s.tier == t["id"]]
        if not rows:
            continue
        blocks.append({
            "tier": t["id"], "tier_label": t["label"],
            "lines": [{
                "text": s.creepy,
                "signal_id": s.id,
                "source": s.source,
                "source_label": s.source_label,
                "vendor": s.vendor,
                "cost": s.cost,
                "creepiness": s.creepiness,
                "would_hold": s.surface == SurfacePolicy.HOLD,
            } for s in rows],
        })
    return {"headline": headline, "blocks": blocks}


# --------------------------------------------------------------------------- #
# The provenance ledger — every signal in the catalog + what we did with it.
# --------------------------------------------------------------------------- #
def _disposition(s: Signal, available: bool, mode: str) -> str:
    if not available:
        return LOCKED
    if mode == "creepy":
        return SHOWN
    if s.surface == SurfacePolicy.SAY:
        return SAID
    if s.surface == SurfacePolicy.ALLUDE:
        return STEER
    return WITHHELD


def _ledger(avail_ids: set[str], mode: str) -> list[dict]:
    rows = []
    for s in S.CATALOG:
        available = s.id in avail_ids
        rows.append({
            "id": s.id, "label": s.label, "value": s.value,
            "source": s.source, "source_label": s.source_label,
            "vendor": s.vendor, "how": s.how, "tier": s.tier,
            "cost": s.cost, "basis": s.basis, "creepiness": s.creepiness,
            "surface": s.surface.value,
            "disposition": _disposition(s, available, mode),
        })
    return rows


def build(tier: str = "anonymous", mode: str = "tasteful") -> dict:
    """Render the whole demo state for one (tier, mode).

    Returns the persona, the chosen tier/mode, the rendered page (tasteful or creepy),
    the full provenance ledger, the per-source breakdown, and the "what just unlocked"
    delta for the current tier.
    """
    if tier not in S.TIER_ORDER:
        tier = "anonymous"
    if mode not in ("tasteful", "creepy"):
        mode = "tasteful"

    avail = S.available_at(tier)
    avail_ids = {s.id for s in avail}

    page = _creepy_copy(avail) if mode == "creepy" else _tasteful_copy(avail_ids)
    ledger = _ledger(avail_ids, mode)

    # counts that make the contrast legible
    counts = {
        "available": len(avail),
        "total": len(S.CATALOG),
        "said": sum(1 for r in ledger if r["disposition"] == SAID),
        "steer": sum(1 for r in ledger if r["disposition"] == STEER),
        "withheld": sum(1 for r in ledger if r["disposition"] == WITHHELD),
        "shown": sum(1 for r in ledger if r["disposition"] == SHOWN),
        "locked": sum(1 for r in ledger if r["disposition"] == LOCKED),
        "max_creep": max([s.creepiness for s in avail], default=0),
        "paid": sum(1 for s in avail if s.source in (S.BROKER, S.IDENTITY_GRAPH)),
    }

    # per-source rollup (how many facts each provenance class contributes, at this tier)
    by_source = []
    for kind, meta in S.SOURCE_META.items():
        got = [s for s in avail if s.source == kind]
        by_source.append({
            "kind": kind, "label": meta["label"], "where": meta["where"],
            "cost": meta["cost"], "color": meta["color"],
            "count": len(got), "any": bool(got),
        })

    return {
        "persona": S.PERSONA,
        "tier": tier, "tier_label": S.TIER_BY_ID[tier]["label"],
        "mode": mode,
        "tiers": [{"id": t["id"], "label": t["label"], "login": t["login"],
                   "blurb": t["blurb"]} for t in S.TIERS],
        "tier_order": S.TIER_ORDER[tier],
        "page": page,
        "ledger": ledger,
        "by_source": by_source,
        "unlocked_here": [{"label": s.label, "value": s.value, "source_label": s.source_label,
                           "creepiness": s.creepiness} for s in S.unlocked_by(tier)],
        "counts": counts,
    }
