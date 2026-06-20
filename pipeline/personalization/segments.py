"""Segmentation engine — derive a customer's segments (with evidence), pick a UI archetype,
and explain exactly how the landing page was built.

Eight segment families, grouped: the three the operator named (behavioral, preferential,
lifestage) + five added (professional, intent, economic, channel, psychographic). Each
derived segment records its evidence — which data point, from which source — so the admin
"how this page was built" view is fully traceable. Segments then select one of six UI
archetypes (layout + theme), and the context tier (1–4) governs how personal the copy goes.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Segment families (for display + grouping)
# --------------------------------------------------------------------------- #
FAMILIES = [
    ("behavioral", "Behavioral — how they've engaged", "HubSpot + observed"),
    ("preferential", "Preferential — what they value", "declared goal + pages"),
    ("lifestage", "Lifestage — where they are in their career", "LinkedIn + declared"),
    ("professional", "Professional / firmographic", "LinkedIn (public)"),
    ("intent", "Intent / readiness", "HubSpot lead score"),
    ("economic", "Economic / value", "HubSpot (+ broker, greyed)"),
    ("channel", "Channel / device / context", "observed"),
    ("psychographic", "Psychographic / motivation", "inferred"),
]

# --------------------------------------------------------------------------- #
# UI archetypes — segments map to one of these (layout + theme + content order)
# --------------------------------------------------------------------------- #
ARCHETYPES = {
    "outcomes_first": {"label": "Outcomes-first", "accent": "#2bb673", "hero": "outcome",
                       "sections": ["outcomes", "curriculum", "financing"],
                       "cta": "See graduate outcomes →", "density": "normal",
                       "for": "career-switchers who care about the payoff"},
    "cost_confident": {"label": "Cost-confident", "accent": "#0e9bab", "hero": "financing",
                       "sections": ["financing", "outcomes", "curriculum"],
                       "cta": "See payment & scholarship options →", "density": "normal",
                       "for": "the budget-conscious"},
    "fast_track": {"label": "Fast-track", "accent": "#8a5cf6", "hero": "apply",
                   "sections": ["curriculum", "outcomes", "start-dates"],
                   "cta": "Apply now →", "density": "dense",
                   "for": "ready, technical, high-intent"},
    "explorer": {"label": "Explorer", "accent": "#4cc4d4", "hero": "intro",
                 "sections": ["what-you-learn", "stories"],
                 "cta": "Watch a free class →", "density": "airy",
                 "for": "just browsing"},
    "welcome_back": {"label": "Welcome-back", "accent": "#d98a16", "hero": "welcome",
                     "sections": ["next-step", "whats-new"],
                     "cta": "Continue your path →", "density": "normal",
                     "for": "existing customers"},
    "prestige": {"label": "Prestige", "accent": "#7e8ea3", "hero": "credibility",
                 "sections": ["credibility", "outcomes", "instructors"],
                 "cta": "Talk to admissions →", "density": "normal",
                 "for": "senior leaders"},
}

# --------------------------------------------------------------------------- #
# Context tiers 1–4 (how personal the copy goes — reuses the surface policy)
# --------------------------------------------------------------------------- #
TIERS = {
    1: {"label": "Safe", "uses": "declared + public professional", "policy": "say only"},
    2: {"label": "Warm", "uses": "+ first-party HubSpot behavior", "policy": "+ allude"},
    3: {"label": "Inferred", "uses": "+ modeled segments", "policy": "inferred, source hidden"},
    4: {"label": "Creepy", "uses": "+ deep OAuth / broker / identity graph", "policy": "surface policy OFF"},
}


def _seg(sid, label, *evidence):
    return {"id": sid, "label": label, "evidence": list(evidence)}


def derive(p: dict) -> dict:
    """Return {family: {label, source, segments:[{id,label,evidence}]}} for a person."""
    li, hs, dec, deep = p["linkedin"], p["hubspot"], p["declared"], p["deep"]
    goal = dec.get("goal", "").lower()
    pages = " ".join(hs.get("top_pages", []))
    score = hs.get("lead_score", 0)
    out: dict = {}

    def add(fam, *segs):
        meta = next(f for f in FAMILIES if f[0] == fam)
        out[fam] = {"label": meta[1], "source": meta[2], "segments": [s for s in segs if s]}

    # behavioral
    temp = ("hot" if hs["lifecycle"] in ("sql",) or score >= 80 else
            "warm" if hs["lifecycle"] in ("mql", "customer") or score >= 45 else "new")
    beh = [_seg(temp, {"hot": "Hot", "warm": "Warm", "new": "New"}[temp],
                f"HubSpot lifecycle={hs['lifecycle']}", f"lead score {score}", f"{hs['visits']} visits")]
    if hs.get("abandoned"):
        beh.append(_seg("abandoned", "Abandoned action", f"HubSpot: abandoned {hs['abandoned']}"))
    add("behavioral", *beh)

    # preferential
    pref = []
    if any(w in goal for w in ("salary", "job", "career", "double", "outcome")) or "outcomes" in pages or "salary" in pages:
        pref.append(_seg("outcomes", "Outcome-driven", "goal mentions career/salary", f"pages: {pages}"))
    if any(w in goal for w in ("afford", "broke", "cost", "cheap")) or any(w in pages for w in ("financing", "pricing", "scholarship")):
        pref.append(_seg("cost", "Cost-conscious", "goal/pages mention affordability"))
    if any(w in goal for w in ("night", "break", "around", "weekend")) or "schedule" in pages:
        pref.append(_seg("flexibility", "Flexibility-seeking", "goal/pages mention schedule"))
    if li["seniority"] in ("exec",) or any(w in pages for w in ("instructors", "enterprise", "credibility")):
        pref.append(_seg("prestige", "Prestige-oriented", f"LinkedIn seniority={li['seniority']}"))
    add("preferential", *(pref or [_seg("general", "General interest", "no strong signal")]))

    # lifestage
    life = []
    if li["seniority"] in ("returner",) or "return" in goal or deep.get("life_event") == "returning to work":
        life.append(_seg("returner", "Career returner", "LinkedIn: career break"))
    elif li["seniority"] == "new_grad":
        life.append(_seg("new_grad", "New grad", "LinkedIn: new grad"))
    elif (not li["technical"]) or li["seniority"] == "career_change" or any(w in goal for w in ("switch", "into", "change")):
        life.append(_seg("career_switcher", "Career-switcher", f"LinkedIn title={li['title']}", "declared goal"))
    else:
        life.append(_seg("upskiller", "Upskiller", f"LinkedIn: {li['tenure']}y, technical"))
    add("lifestage", *life)

    # professional
    add("professional",
        _seg("technical" if li["technical"] else "non_technical",
             "Technical" if li["technical"] else "Non-technical", f"LinkedIn title={li['title']}"),
        _seg(li["seniority"], li["seniority"].replace("_", " ").title(),
             f"LinkedIn seniority={li['seniority']}", f"{li['tenure']}y tenure", f"industry={li['industry']}"))

    # intent
    intent = ("ready" if score >= 75 or hs["lifecycle"] == "sql" or hs.get("abandoned") else
              "researching" if score >= 40 else "browsing")
    add("intent", _seg(intent, intent.title(), f"lead score {score}", f"lifecycle={hs['lifecycle']}"))

    # economic
    econ = []
    if hs.get("past_customer"):
        econ.append(_seg("past_customer", "Past customer", "HubSpot: prior purchase"))
    low_income = deep.get("income_band", "").startswith("<") or "40K" in deep.get("income_band", "")
    if any(s["id"] == "cost" for s in out["preferential"]["segments"]) or low_income:
        econ.append(_seg("price_sensitive", "Price-sensitive", "cost signals + modeled income (synthetic)"))
        if low_income:
            econ.append(_seg("scholarship_likely", "Scholarship-likely", "modeled income low (synthetic, deep tier)"))
    add("economic", *(econ or [_seg("standard", "Standard value", "no strong signal")]))

    # channel
    add("channel",
        _seg(deep.get("device", "desktop"), deep.get("device", "desktop").title(), "observed device"),
        _seg("src_" + hs.get("source", "direct"), f"From {hs.get('source', 'direct')}", f"HubSpot source={hs.get('source')}"),
        _seg("dp_" + deep.get("daypart", "day").split()[0], deep.get("daypart", "day").title(), "observed local time"))

    # psychographic
    psy = []
    psy.append(_seg("ambitious" if any(w in goal for w in ("fast", "double", "lead", "first")) else "steady",
                    "Ambitious" if any(w in goal for w in ("fast", "double", "lead", "first")) else "Steady",
                    "goal tone"))
    psy.append(_seg("data_driven" if li["technical"] else "social_proof",
                    "Data-driven" if li["technical"] else "Social-proof-led", "LinkedIn technical flag"))
    add("psychographic", *psy)
    return out


def _has(segs: dict, fam: str, sid: str) -> bool:
    return any(s["id"] == sid for s in segs.get(fam, {}).get("segments", []))


def pick_archetype(p: dict, segs: dict) -> dict:
    """Map segments → one of six archetypes, with the deciding reason."""
    if _has(segs, "economic", "past_customer"):
        a, why = "welcome_back", "existing customer (HubSpot)"
    elif _has(segs, "intent", "browsing"):
        a, why = "explorer", "cold / just browsing (low lead score)"
    elif _has(segs, "intent", "ready") and _has(segs, "professional", "technical"):
        a, why = "fast_track", "ready-to-apply + technical"
    elif _has(segs, "professional", "exec") or _has(segs, "preferential", "prestige"):
        a, why = "prestige", "senior leader / prestige-oriented"
    elif _has(segs, "economic", "price_sensitive"):
        a, why = "cost_confident", "price-sensitive"
    elif _has(segs, "preferential", "outcomes") or _has(segs, "lifestage", "career_switcher") or _has(segs, "lifestage", "returner"):
        a, why = "outcomes_first", "outcome-driven career-switcher"
    else:
        a, why = "explorer", "low intent / just browsing"
    return {"id": a, "reason": why, **ARCHETYPES[a]}


def explain(p: dict, tier: int = 2) -> dict:
    """The full 'how this page was built' record for the admin view."""
    segs = derive(p)
    arch = pick_archetype(p, segs)
    raw = p.get("_raw")
    if raw:
        v, hs, cl = raw["vector"], raw["hubspot"], raw["clay"]
        hub = (f"{hs['role']} · “{hs['interest_reason']}” · {hs['lifecycle']} · score {hs['lead_score']}"
               if hs.get("submitted") else
               f"no form submitted · {hs['lifecycle']} · {hs['visits']} visit(s) · {hs['source']}")
        data_points = [
            {"label": "Vector — de-anonymized traffic", "source": "vector",
             "value": " · ".join(x for x in [v['job_title'], v['company'], v['org_type'],
                                             v['company_size'], v['location']] if x)},
            {"label": "HubSpot — form + CRM", "value": hub, "source": "hubspot"},
            {"label": "Clay — enrichment", "source": "clay",
             "value": " · ".join(x for x in [cl['seniority'], f"{cl['tenure']}y",
                                 'technical' if cl['technical'] else 'non-technical', cl['industry'],
                                 (f"modeled income {cl['income_band']}" if cl.get('income_band') else "")] if x)},
        ]
    else:
        li, hs, dec = p["linkedin"], p["hubspot"], p["declared"]
        data_points = [
            {"label": "LinkedIn", "value": f"{li['title']} · {li['seniority']}", "source": "vector"},
            {"label": "HubSpot", "value": f"{hs['lifecycle']} · score {hs['lead_score']}", "source": "hubspot"},
            {"label": "Declared", "value": f"“{dec['goal']}”", "source": "clay"},
        ]
    ui_levers = [f"theme accent {arch['accent']}", f"hero: {arch['hero']}",
                 "section order: " + " → ".join(arch["sections"]), f"CTA: {arch['cta']}",
                 f"density: {arch['density']}"]
    return {"segments": segs, "archetype": arch, "data_points": data_points,
            "ui_levers": ui_levers, "tier": tier, "tier_meta": TIERS[tier]}
