"""Showcase use-case demos — four go-to-market shapes, each a real page on the live engine.

Every use case renders the SAME normalized view-model so the template stays generic:
  production : {gated, ungated}   — the version that ships vs the one the Gate blocks
  sections   : [{title, rows}]    — the inputs / decisions / provenance, as rows
  gate       : [{verdict, line, why}]
  trace      : [{n, name, detail}]

The four kinds are powered by different real engines:
  1 · GauntletAI (firmographic) — scene.build_scene: IP → industry/region → copy + backdrop
  2 · SkyFi      (firmographic) — same engine, geo/sector framing
  3 · Known      (known)        — persuasion.build_plan: a Gate-bounded persuasion play
  4 · Optimizer  (optimizer)    — demo_sim.build: the truth-bounded bandit (can't win by lying)
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.common.schemas import Recipient
from pipeline.personalization import creative as CR
from pipeline.personalization import scene as SC


@dataclass(frozen=True)
class UseCaseDemo:
    slug: str
    num: int
    brand: str
    domain: str
    category: str
    accent: str
    kind: str                   # firmographic | known | optimizer
    default_industry: str
    summary: str
    what_apt_does: str
    angle: dict                 # GATED copy (firmographic only)
    say_angle: dict             # UNGATED copy (firmographic only)


DEMOS: dict[str, UseCaseDemo] = {
    "gauntletai": UseCaseDemo(
        slug="gauntletai", num=1, brand="GauntletAI", domain="gauntletai.com",
        category="AI engineering training", accent="#7c5cff", kind="firmographic",
        default_industry="technology",
        summary="An anonymous visitor → a hero rewritten for their company, industry, and region.",
        what_apt_does=(
            "A first-time visitor lands with no identity. apt resolves their company, industry "
            "and region from the IP — before the page paints — and reframes GauntletAI's pitch to "
            "that exact team. Nothing the visitor didn't earn is recited; every line carries a receipt."),
        angle={
            "eyebrow": "For {industry} teams in {region}",
            "headline": "Your {industry} team is one cohort away from building with AI.",
            "sub": "Gauntlet trains {industry} engineers to ship with AI in 10 weeks — not 10 hires. "
                   "Built around how {region} teams actually work.",
            "cta": "See the {industry} track"},
        say_angle={
            "eyebrow": "Resolved from your IP",
            "headline": "{company} in {city} — one cohort from building with AI.",
            "sub": "We pulled your company and your office from your IP. Most {industry} teams near "
                   "{city} already train with us."}),
    "skyfi": UseCaseDemo(
        slug="skyfi", num=2, brand="SkyFi", domain="skyfi.com",
        category="on-demand satellite imagery", accent="#1E6FA8", kind="firmographic",
        default_industry="mining",
        summary="A geo-pinned operator → copy and a backdrop tuned to their region and sector.",
        what_apt_does=(
            "A geography-dependent operator lands on the site. apt detects the business and its "
            "region + sector and tailors the copy — and the backdrop — to that operation. It frames "
            "the region, but won't pinpoint the exact site unless the visitor declares it."),
        angle={
            "eyebrow": "For {industry} operations across {region}",
            "headline": "See change across your {region} sites — on a weekly cadence.",
            "sub": "SkyFi delivers on-demand satellite imagery tuned to {industry} operators. "
                   "Point us at your area of interest; we image it.",
            "cta": "Image your {region} operations"},
        say_angle={
            "eyebrow": "Resolved from your IP",
            "headline": "{company} — we see your {industry} sites near {city}, {region}.",
            "sub": "Down to the parcel. We imaged your exact area of interest already — want the same "
                   "cadence on your operations?"}),
    "known": UseCaseDemo(
        slug="known", num=3, brand="Known customer", domain="email / magic-link",
        category="close the sale", accent="#d98a16", kind="known", default_industry="",
        summary="A known visitor → a Gate-bounded persuasion play that surfaces only provable claims.",
        what_apt_does=(
            "A known visitor (email match or magic-link) resolves to a person + account + behavior. "
            "apt picks a persuasion principle and closes with only claims it can prove — held claims "
            "are dropped, and sensitive PII steers the angle but is never recited."),
        angle={}, say_angle={}),
    "optimizer": UseCaseDemo(
        slug="optimizer", num=4, brand="Long-running A/B", domain="reinforcement learning",
        category="truth-bounded optimization", accent="#2bb673", kind="optimizer", default_industry="",
        summary="A bandit that learns the best variant over time — and can't win by lying.",
        what_apt_does=(
            "Over many visits the bandit learns which framing converts per segment from real "
            "outcomes. It can only ever pull Gate-cleared arms, so the planted lie — the highest "
            "engagement of all — is structurally unservable. Lift is measured against a random control."),
        angle={}, say_angle={}),
}
ORDER = ["gauntletai", "skyfi", "known", "optimizer"]


# --- helpers ----------------------------------------------------------------
def _fill(t: str, industry_label: str | None, region: str | None) -> str:
    return t.replace("{industry}", (industry_label or "your").lower()).replace("{region}", region or SC.GENERIC_REGION)


def _fill_say(t: str, *, company, city, industry_label, region) -> str:
    return (t.replace("{company}", company or "your company").replace("{city}", city or "your city")
             .replace("{industry}", (industry_label or "your").lower()).replace("{region}", region or SC.GENERIC_REGION))


def _rich_vm(demo, *, site, img, sections, impact, ungated_hero, obs_sections, gate, trace,
             personas, active_persona, active_ip="", active_industry="", active_region="",
             ungated_note="recites involuntary data", ip_label="or an IP") -> dict:
    """The normalized rich view-model — the same shape `use_case_rich.html` renders for every kind."""
    return {"demo": demo, "kind": demo.kind, "site": site, "img": img, "sections": sections,
            "impact": impact, "ungated_hero": ungated_hero, "obs_sections": obs_sections,
            "gate": gate, "trace": trace, "personas": personas, "active_persona": active_persona,
            "active_ip": active_ip, "active_industry": active_industry, "active_region": active_region,
            "examples": SC.EXAMPLE_ACCOUNTS, "loc_detected": True, "ungated_note": ungated_note,
            "ip_label": ip_label, "demos": [DEMOS[s] for s in ORDER]}


def _impact(sections, signals, *, lift_label, lift_note) -> dict:
    return {"blocks": len(sections), "signals": signals, "recited": 0,
            "lift_label": lift_label, "lift_note": lift_note}


# --- kind: firmographic (UC1, UC2) — rich, multi-section, persona-driven -----
_SIZE_LABEL = {"startup": "Early-stage", "mid": "Growing", "enterprise": "Enterprise"}
_ROLE_LABEL = {"founder": "Founder", "exec": "Executive", "technical": "Technical leader", "ops": "Operator"}
_INTENT_LABEL = {"hiring": "Hiring", "expansion": "Expanding"}

# Curated personas for the switcher — rich signals an IP alone can't give (size / role / intent).
PERSONAS: dict[str, list[dict]] = {
    "gauntletai": [
        {"key": "vp_bank", "label": "VP Eng · F500 bank · New York", "sub": "enterprise · technical · expanding",
         "industry": "technology", "region": "New York", "size": "enterprise", "role": "technical", "intent": "expansion"},
        {"key": "founder_sf", "label": "Founder · seed startup · California", "sub": "startup · founder · hiring",
         "industry": "technology", "region": "California", "size": "startup", "role": "founder", "intent": "hiring"},
        {"key": "health_data", "label": "Head of Data · hospital net · Texas", "sub": "growing · technical",
         "industry": "healthcare", "region": "Texas", "size": "mid", "role": "technical", "intent": ""},
    ],
    "skyfi": [
        {"key": "mine_gm", "label": "Mine GM · large operator · Arizona", "sub": "enterprise · ops · expanding",
         "industry": "mining", "region": "Arizona", "size": "enterprise", "role": "ops", "intent": "expansion"},
        {"key": "ag_coop", "label": "Precision-ag dir · co-op · Iowa", "sub": "growing · ops",
         "industry": "agriculture", "region": "Iowa", "size": "mid", "role": "ops", "intent": ""},
        {"key": "build_pm", "label": "Construction PM · regional · Texas", "sub": "growing · ops · expanding",
         "industry": "construction", "region": "Texas", "size": "mid", "role": "ops", "intent": "expansion"},
    ],
}

# UC3 personas are *known accounts* — the resolving signal is identity (email / magic-link),
# not an IP. Each drives a different lifecycle, role, persuasion strategy, and held-PII recite.
PERSONAS["known"] = [
    {"key": "cfo_idn", "label": "CFO · hospital network · returning", "sub": "abandoned mid-evaluation",
     "name": "Maya Chen", "company": "Northwind Health", "role": "cfo", "size": "idn", "region": "West",
     "industry": "healthcare", "use_case": "lower total cost of ownership", "urgency": "high",
     "signals": {"returning": True, "abandoned": True}, "income": "$190K", "behavior": "abandoned application (step 3)"},
    {"key": "ciso_idn", "label": "CISO · health system · evaluating", "sub": "technical buyer · first visit",
     "name": "Dev Okafor", "company": "Cedar Ridge Health", "role": "it_security", "size": "idn", "region": "South",
     "industry": "healthcare", "use_case": "pass security review", "urgency": "medium",
     "signals": {}, "income": "$240K", "behavior": "downloaded the SOC 2 packet"},
    {"key": "clinops_comm", "label": "Clin-ops lead · community clinic · urgent", "sub": "renewal window closing",
     "name": "Rosa Vega", "company": "Brightside Clinics", "role": "clinops", "size": "community", "region": "West",
     "industry": "healthcare", "use_case": "cut length of stay", "urgency": "high",
     "signals": {}, "income": "$120K", "behavior": "opened 4 renewal emails, no reply"},
]

# UC4 personas are *segments* — the bandit learns a winning arm per segment over real traffic.
# Each maps to one of the three live /demo scenarios (its arms, learned winner, and blocked lie).
PERSONAS["optimizer"] = [
    {"key": "anon", "label": "Segment · new anonymous viewer", "sub": "cold IP signals", "sid": "A"},
    {"key": "customer", "label": "Segment · existing customer", "sub": "CRM + behaviour", "sid": "B"},
    {"key": "lead", "label": "Segment · emailed lead", "sub": "magic-link click", "sid": "C"},
]


def persona(slug: str, key: str) -> dict | None:
    return next((p for p in PERSONAS.get(slug, []) if p["key"] == key), None)


def _persona_or_first(slug: str, key: str) -> dict:
    ps = PERSONAS.get(slug, [])
    return next((p for p in ps if p["key"] == key), ps[0]) if ps else {}


def _firmo_sections(slug: str, cx: dict) -> list[dict]:
    """The page's blocks, each with a personalized (p) and generic (g) version + the signal that drove it."""
    ind, reg = cx["ind_label"].lower(), cx["region"]
    size, role, intent = cx["size"], cx["role"], cx["intent"]
    sizew = _SIZE_LABEL.get(size, "")
    tech = role in ("technical", "ops")
    if slug == "gauntletai":
        hero_p = {"eyebrow": f"For {ind} teams in {reg}", "headline": f"Your {ind} team is one cohort from building with AI.",
                  "sub": f"Gauntlet trains {ind} engineers in {reg} to ship with AI in 10 weeks — not 10 hires.", "cta": f"See the {ind} track"}
        hero_g = {"eyebrow": "For engineering teams", "headline": "Train your team to build with AI.",
                  "sub": "A rigorous, hands-on AI engineering program.", "cta": "See the program"}
        proof_p = {"headline": f"{sizew} {ind} teams already ship with Gauntlet.".strip(),
                   "sub": f"Engineering leaders across {reg} send their teams here.", "chips": [f"a {ind} team", f"a {reg} org", "10-week cohort"]}
        proof_g = {"headline": "Trusted by engineering teams.", "sub": "Across industries.", "chips": ["—", "—", "—"]}
        feat_p = ({"headline": "Build the real thing.", "sub": "Agents, RAG, evals, and deploys — graded on systems that run, not slides."} if tech
                  else {"headline": "Outcomes you can measure.", "sub": "Your team ships a working AI system in 10 weeks — not after 10 senior hires."})
        feat_g = {"headline": "A hands-on curriculum.", "sub": "Project-based AI engineering."}
        if size == "enterprise":
            offer_p = {"headline": "Cohorts for whole teams.", "sub": "Custom onboarding and a dedicated lead.", "cta": "Talk to our team"}
        elif size == "startup":
            offer_p = {"headline": "Start with one engineer.", "sub": "First module free — see the bar before you commit.", "cta": "Start free"}
        else:
            offer_p = {"headline": "Bring your team up fast.", "sub": "Flexible cohorts for growing teams.", "cta": "See cohorts"}
        if intent == "hiring":
            offer_p["sub"] = "Hiring senior AI talent is brutal — train the team you have. " + offer_p["sub"]
        elif intent == "expansion":
            offer_p["sub"] = "Scaling fast? Get your team building now. " + offer_p["sub"]
        offer_g = {"headline": "Enroll today.", "sub": "Join the next cohort.", "cta": "Enroll"}
        cat_p = {"headline": "Outcomes, not certificates.", "sub": "Every grad ships a working system — and every claim on this page carries its source."}
        cat_g = {"headline": "Why Gauntlet.", "sub": "A different kind of program."}
    else:  # skyfi
        hero_p = {"eyebrow": f"For {ind} operations across {reg}", "headline": f"See change across your {reg} {ind} sites — weekly.",
                  "sub": f"On-demand satellite imagery tuned to {ind} operators in {reg}.", "cta": f"Image your {reg} sites"}
        hero_g = {"eyebrow": "On-demand satellite imagery", "headline": "See your sites from above, on demand.",
                  "sub": "Fresh, licensed satellite imagery.", "cta": "Get imagery"}
        proof_p = {"headline": f"{sizew} {ind} operators run on SkyFi.".strip(),
                   "sub": f"Teams across {reg} monitor their sites with us.", "chips": [f"a {ind} operator", f"a {reg} co-op", "fleet coverage"]}
        proof_g = {"headline": "Trusted by operators.", "sub": "Across sectors.", "chips": ["—", "—", "—"]}
        feat_p = {"headline": f"Tuned to {ind}.", "sub": "Tasking, change-detection, and alerts on the cadence your operation needs."}
        feat_g = {"headline": "Imagery, on demand.", "sub": "Task a satellite, get the image."}
        if size == "enterprise":
            offer_p = {"headline": "Fleet-wide coverage.", "sub": "Every site, one dashboard, a dedicated lead.", "cta": "Talk to our team"}
        else:
            offer_p = {"headline": "Image one site, on demand.", "sub": "Pay per capture — no subscription to start.", "cta": "Image a site"}
        if intent == "expansion":
            offer_p["sub"] = "Breaking ground on new sites? Baseline them from orbit. " + offer_p["sub"]
        offer_g = {"headline": "Get started.", "sub": "Order imagery today.", "cta": "Order"}
        cat_p = {"headline": "Fresh and licensed — not last year's basemap.", "sub": "Every image dated and sourced; every line on this page carries its provenance."}
        cat_g = {"headline": "Why SkyFi.", "sub": "On-demand, high-resolution."}
    return [
        {"id": "hero", "label": "Hero", "tag": "industry · region · role", "p": hero_p, "g": hero_g},
        {"id": "proof", "label": "Peer proof", "tag": "industry · company size", "p": proof_p, "g": proof_g},
        {"id": "features", "label": "What you get", "tag": "role", "p": feat_p, "g": feat_g},
        {"id": "offer", "label": "Offer", "tag": "company size · intent", "p": offer_p, "g": offer_g},
        {"id": "category", "label": "Why us", "tag": "category · provable", "p": cat_p, "g": cat_g},
    ]


def _build_firmographic(slug: str, det: dict, octx: dict) -> dict:
    d = DEMOS[slug]
    ind, region = octx["industry"], octx["region"]
    company, city, detected = octx["company"], octx["city"], octx["detected"]
    size, role, intent = octx.get("size", ""), octx.get("role", ""), octx.get("intent", "")
    label = SC.BY_KEY.get(ind, SC.BY_KEY[SC.DEFAULT_INDUSTRY])["label"]
    img = SC.image_for(ind)
    cx = {"ind": ind, "ind_label": label, "region": region or "your region",
          "size": size, "role": role, "intent": intent, "company": company, "city": city}
    sections = _firmo_sections(slug, cx)

    signals_used: list[dict] = []

    def _sig(name, val, src, drives):
        if val:
            signals_used.append({"name": name, "value": val, "source": src, "drives": drives})
    _sig("Industry", label, "reverse-IP / PDL", "hero · proof · features · imagery")
    _sig("Region", region, "geo-IP", "hero · proof · local framing")
    _sig("Company size", _SIZE_LABEL.get(size), "enrichment / declared", "the offer + proof scale")
    _sig("Role / seniority", _ROLE_LABEL.get(role), "enrichment / declared", "feature framing")
    _sig("Buying intent", _INTENT_LABEL.get(intent), "intent signals", "urgency in the offer")

    impact = {"blocks": len(sections), "signals": len(signals_used), "recited": 0,
              "lift_label": "1.5–3× conversion vs a generic page",
              "lift_note": "illustrative benchmark for relevance-matched landing pages — not a measured result on this page"}

    ungated_hero = {"eyebrow": "Resolved from your IP",
                    "headline": _fill_say(d.say_angle["headline"], company=company, city=city, industry_label=label, region=region),
                    "sub": _fill_say(d.say_angle["sub"], company=company, city=city, industry_label=label, region=region),
                    "cta": sections[0]["p"]["cta"], "image": img["url"], "attr": img}

    captured = [{"k": r["label"], "v": r["value"], "conf": r.get("conf"), "meta": f"{r['policy']} · {r['drives']}"}
                for r in (det.get("captured") or [])]
    captured += [{"k": r["label"], "v": r["value"], "meta": f"{r['policy']} · {r['drives']}"} for r in det.get("request_signals", [])]
    conf = det.get("confidence", {})
    routing = [{"k": "Network type", "v": det.get("network_type", "—")},
               {"k": "Personalization tier", "v": f"{det.get('tier', 0)} · {det.get('tier_label', '—')}"},
               {"k": "Confidence", "v": f"location {conf.get('location','—')} · company {conf.get('company','—')} · industry {conf.get('industry','—')}"}]
    if det.get("reason"):
        routing.append({"k": "Why", "v": det["reason"]})
    scene = SC.build_scene(region, ind, detected=detected, company=company, city=city, policy="allude")
    prov = [{"k": r["signal"], "v": r["role"], "meta": f"{r['policy']} · {r['source']}"} for r in scene["receipt"]]
    obs_sections = [
        {"title": "Inputs — signals captured", "icon": "ph-traffic-signal", "mode": detected,
         "rows": captured or [{"k": "Local / private IP", "v": "enter a public IP above, or pick an example account", "meta": "no capture"}]},
        {"title": "Routing decision — deterministic, no LLM", "icon": "ph-git-fork", "rows": routing},
        {"title": "Page assembly — block ← signal", "icon": "ph-stack",
         "rows": [{"k": s["label"], "v": s["p"]["headline"], "meta": "from " + s["tag"]} for s in sections]},
        {"title": "Provenance — what touched the page", "icon": "ph-seal-check", "rows": prov}]
    ai = CR.ai_copy(industry=ind, region=region, company=company, city=city, angle="default", policy="allude")
    gchk = CR.verify_copy([sections[0]["p"]["headline"], sections[0]["p"]["sub"]], "", company, "allude")
    gate = [{"verdict": "ok" if ai["ships"] else "block", "line": ai["headline"], "why": "proposed hero — agent → Gate"}]
    gate += [{"verdict": "ok", "line": ck["line"], "why": f"gated — {ck['reason']}"} for ck in gchk]
    gate += [{"verdict": "block", "line": ungated_hero["headline"], "why": "ungated — recites company / precise location (say policy)"},
             {"verdict": "block", "line": ai["blocked_example"]["line"], "why": ai["blocked_example"]["reason"]}]
    trace = [
        {"n": 1, "name": "Resolve", "detail": f"IP → region {scene['region']}" + (f", company {company}" if company else ", no company")},
        {"n": 2, "name": "Classify", "detail": f"network {det.get('network_type','—')} · tier {det.get('tier',0)} · {det.get('tier_label','—')}"},
        {"n": 3, "name": "Enrich", "detail": f"industry → {label}; size/role/intent → {', '.join(s['value'] for s in signals_used[2:]) or 'not from IP (use a persona)'}"},
        {"n": 4, "name": "Assemble", "detail": f"{len(sections)} blocks personalized from {len(signals_used)} signals"},
        {"n": 5, "name": "Gate", "detail": "every block provable; the recite version blocked"},
        {"n": 6, "name": "Receipt", "detail": f"{len(scene['receipt'])} sources bound · 0 recited"}]

    return {"demo": d, "kind": "firmographic", "site": d.brand, "img": img, "sections": sections, "impact": impact,
            "signals_used": signals_used, "ungated_hero": ungated_hero, "personas": PERSONAS.get(slug, []),
            "examples": SC.EXAMPLE_ACCOUNTS, "active_persona": octx.get("persona", ""), "active_ip": octx.get("ip", ""),
            "ctx": cx, "det": det, "loc_detected": detected, "active_industry": ind, "active_region": region or "",
            "ungated_note": "recites company / precise location", "ip_label": "or an IP",
            "obs_sections": obs_sections, "gate": gate, "trace": trace, "demos": [DEMOS[s] for s in ORDER]}


# --- kind: known customer (UC3) — rich, multi-section, account-driven --------
_KNOWN_SITE = "Helix Health"
_ROLE_PEER = {"cfo": "Finance leaders at health systems", "it_security": "Security leaders at health networks",
              "clinops": "Clinical-ops leaders at care organizations", "quality": "Quality leaders at care orgs"}


def _known_sections(p: dict, r: Recipient, plan, *, region: str, company, city) -> list[dict]:
    """The same 5-block landing as firmographic, but driven by identity + the Gate-bounded plan."""
    first = r.name.split()[0]
    strat = plan.strategy.replace("_", " ")
    lead = plan.claims[0]["text"] if plan.claims else "verified, independently sourced results"
    returning = bool(p["signals"].get("returning") or p["signals"].get("abandoned"))
    peer = _ROLE_PEER.get(r.role, "Leaders at health organizations")
    reg = region or "your region"
    hero_p = {"eyebrow": f"{strat} · welcome back, {first}" if returning else f"{strat} · for {first}",
              "headline": plan.headline,
              "sub": (f"You paused mid-evaluation — so we resume with proof, not pressure. " if returning
                      else f"You came in on {r.use_case} — so we lead with proof, not pressure. ")
                     + "Every line here is sourced; anything we can't prove is held back.",
              "cta": plan.cta}
    hero_g = {"eyebrow": "Sign in", "headline": f"Welcome to {_KNOWN_SITE}.",
              "sub": "The clinical platform for modern care teams.", "cta": "Sign in"}
    proof_p = {"headline": f"{peer} like you already run on {_KNOWN_SITE}.",
               "sub": f"Teams across {reg} trust the same proof you're reading — each line carries its source.",
               "chips": [f"a {r.company_size} health org", f"{reg} care teams", "every claim sourced"]}
    proof_g = {"headline": "Trusted by care teams.", "sub": "Across health systems.", "chips": ["—", "—", "—"]}
    feat_p = {"headline": f"Built to {r.use_case}.", "sub": lead}
    feat_g = {"headline": "A clinical platform.", "sub": "For care teams of every size."}
    if returning:
        offer_p = {"headline": "Pick up where you left off.",
                   "sub": f"You stopped at {p['behavior']} — here's the sourced answer waiting for you, {first}.", "cta": plan.cta}
    else:
        offer_p = {"headline": "A tailored, sourced assessment — yours to keep.",
                   "sub": f"Built around {r.use_case}; every figure links to where it came from.", "cta": plan.cta}
    offer_g = {"headline": "Get started.", "sub": "Request a demo.", "cta": "Request a demo"}
    cat_p = {"headline": "Every claim here carries its source.",
             "sub": f"Held claims are dropped, not softened — we surfaced {len(plan.claims)} we can prove and "
                    f"withheld {len(plan.dropped) or 'every line'} we can't."}
    cat_g = {"headline": f"Why {_KNOWN_SITE}.", "sub": "Evidence-based care technology."}
    return [
        {"id": "hero", "label": "Hero", "tag": "identity · lifecycle · strategy", "p": hero_p, "g": hero_g},
        {"id": "proof", "label": "Peer proof", "tag": "role · company size", "p": proof_p, "g": proof_g},
        {"id": "features", "label": "What you get", "tag": "use case · provable claim", "p": feat_p, "g": feat_g},
        {"id": "offer", "label": "Offer", "tag": "on-site behavior", "p": offer_p, "g": offer_g},
        {"id": "category", "label": "Why us", "tag": "provable · held claims dropped", "p": cat_p, "g": cat_g},
    ]


def _build_known(slug: str, gate_obj, library, persona_key: str, overlay: dict,
                 ip: str, industry: str, region: str) -> dict:
    from pipeline.personalization import persuasion
    d = DEMOS[slug]
    p = _persona_or_first(slug, persona_key)
    first = p["name"].split()[0]
    region_eff = region or overlay.get("region") or p["region"]
    company_ov, city_ov = overlay.get("company"), overlay.get("city")
    ind_key = industry or overlay.get("industry") or p["industry"]
    img = SC.image_for(ind_key)
    r = Recipient(recipient_id="kc_" + p["key"], token="kc", name=p["name"],
                  email=f"{first.lower()}@{p['company'].split()[0].lower()}.org", company=p["company"],
                  role=p["role"], company_size=p["size"], region=region_eff,
                  use_case=p["use_case"], urgency=p["urgency"], segment=Recipient.make_segment(p["role"], p["size"]))
    plan = persuasion.build_plan(gate_obj, library, r, signals=p["signals"])
    strat = plan.strategy.replace("_", " ")
    returning = bool(p["signals"].get("returning") or p["signals"].get("abandoned"))
    sections = _known_sections(p, r, plan, region=region_eff, company=company_ov, city=city_ov)

    ungated_hero = {"eyebrow": "CRM + a broker income append",
                    "headline": f"On a {p['income']} income, {r.company} is an easy yes, {first}.",
                    "sub": f"We modeled your household income and saw {p['behavior']} this week.",
                    "cta": "Pay in full", "image": img["url"], "attr": img}

    impact = _impact(sections, len([s for s in sections]),  # 5 blocks, signals counted below
                     lift_label="2–4× reactivation vs a generic welcome-back" if returning
                     else "1.5–3× lead→opportunity vs a generic page",
                     lift_note="illustrative benchmark for identity-matched, proof-led pages — not a measured result on this page")
    n_sig = 4 + (1 if company_ov else 0)
    impact["signals"] = n_sig

    inputs = [{"k": "Email match", "v": r.email, "conf": "declared", "meta": "declared · identity"},
              {"k": "CRM lifecycle", "v": ("customer · returning" if returning else "active evaluation"),
               "meta": "first-party · " + ("welcome-back" if returning else "nurture")},
              {"k": "Behavior", "v": p["behavior"], "meta": "first-party · resume / re-engage"},
              {"k": "Role", "v": f"{p['role'].upper().replace('_',' ')} (PDL)", "meta": "enrich · proof depth"},
              {"k": "Modeled income", "v": f"{p['income']} band", "meta": "broker · HOLD — steers, never recited"}]
    if company_ov:
        inputs.insert(1, {"k": "Company (reverse-IP)", "v": f"{company_ov}" + (f" · {city_ov}" if city_ov else ""),
                          "conf": "high", "meta": "bought · local framing"})
    decision = [{"k": "Strategy", "v": strat}, {"k": "Principle", "v": plan.principle}, {"k": "Rationale", "v": plan.rationale}]
    assembly = [{"k": s["label"], "v": s["p"]["headline"], "meta": "from " + s["tag"]} for s in sections]
    prov = [{"k": c["claim_id"], "v": c["text"], "meta": c["source"]} for c in plan.claims]
    obs_sections = [
        {"title": "Inputs — known-customer signals", "icon": "ph-identification-card", "mode": True, "rows": inputs},
        {"title": "Decision — persuasion strategy", "icon": "ph-strategy", "rows": decision},
        {"title": "Page assembly — block ← signal", "icon": "ph-stack", "rows": assembly},
        {"title": "Provenance — claims surfaced", "icon": "ph-seal-check", "rows": prov}]
    gate = [{"verdict": "ok", "line": c["text"], "why": f"{c['claim_id']} — cleared ({c['source']})"} for c in plan.claims]
    gate += [{"verdict": "block", "line": f"claim {cid}", "why": "blocked by legal hold — dropped from the plan"} for cid in plan.dropped]
    gate += [{"verdict": "block", "line": ungated_hero["headline"], "why": "recites purchased income (broker · HOLD) — overclaim"}]
    trace = [{"n": 1, "name": "Resolve", "detail": f"email / magic-link → {r.name}, {r.role.upper().replace('_',' ')} at {r.company}"},
             {"n": 2, "name": "Enrich", "detail": "CRM lifecycle + behavior + PDL role; broker income (HOLD)"
                      + (f"; reverse-IP → {company_ov}" if company_ov else "")},
             {"n": 3, "name": "Select", "detail": f"persuasion strategy → {strat}"},
             {"n": 4, "name": "Gate", "detail": f"{len(plan.claims)} claims cleared · {len(plan.dropped)} held/dropped"},
             {"n": 5, "name": "Assemble", "detail": f"{len(sections)} blocks personalized; PII held (steers, never shown)"},
             {"n": 6, "name": "Receipt", "detail": f"{len(plan.claims)} claims, each bound to a source"}]
    return _rich_vm(d, site=_KNOWN_SITE, img=img, sections=sections, impact=impact, ungated_hero=ungated_hero,
                    obs_sections=obs_sections, gate=gate, trace=trace, personas=PERSONAS["known"],
                    active_persona=p["key"], active_ip=ip, active_industry=industry or "", active_region=region or "",
                    ungated_note="recites purchased income (HOLD)")


# --- kind: optimizer / RL (UC4) — rich, segment-driven, on the real bandit ---
_OPT_SITE = "Helix Health"


def _opt_sections(scen, sc: dict, win_var, blk_var, *, fill) -> list[dict]:
    """The 5-block landing, where the served hero IS the bandit's learned winner for this segment."""
    share = int(sc.get("winner_share", 0) * 100)
    sigs = ", ".join(du.signal for du in win_var.data_used) if win_var else "the segment's signals"
    hero_p = {"eyebrow": f"{sc['label']} · learned winner ({share}% of pulls)",
              "headline": "The version that wins — and that we can prove.",
              "sub": fill(f"The bandit converged on “{win_var.label}”: {win_var.headline}") if win_var
                     else "The bandit converged on the best Gate-cleared arm.",
              "cta": fill(win_var.cta) if win_var else "Get started"}
    hero_g = {"eyebrow": "Control slice", "headline": fill(f"{_OPT_SITE} — see the platform."),
              "sub": "What a random, un-optimized visitor sees — the baseline the lift is measured against.", "cta": "Get started"}
    proof_p = {"headline": "Learned from real outcomes — not a guess.",
               "sub": f"{share}% of pulls converged on “{win_var.label}”, beating a random control." if win_var
                      else f"{share}% of pulls converged on the winner, beating a random control.",
               "chips": [f"{a['label']} · {a['posterior_mean']}" for a in sc["arms"]]}
    proof_g = {"headline": "An A/B test, running.", "sub": "Results pending.", "chips": ["—", "—", "—"]}
    feat_p = {"headline": "Why this version won.",
              "sub": (fill(win_var.sub) + f" It leads with {sigs}.") if win_var else "It led with the segment's strongest provable signal."}
    feat_g = {"headline": "A standard hero.", "sub": "No signals applied, no learning."}
    offer_p = {"headline": "Served to this segment now.",
               "sub": "The bandit serves only Gate-cleared arms — and updates online from real clicks.",
               "cta": fill(win_var.cta) if win_var else "Get started"}
    offer_g = {"headline": "Get started.", "sub": "One CTA for everyone.", "cta": "Get started"}
    cat_p = {"headline": "It can't win by lying.",
             "sub": (f"The highest-engagement arm of all — “{blk_var.label}” — is an overclaim, so it never enters "
                     "the action pool. Lift is measured against a random control, not asserted.") if blk_var
                    else "The planted lie never enters the action pool; lift is measured, not asserted."}
    cat_g = {"headline": "Why optimize.", "sub": "Find what converts."}
    return [
        {"id": "hero", "label": "Hero", "tag": "segment · learned winner", "p": hero_p, "g": hero_g},
        {"id": "proof", "label": "Peer proof", "tag": "posteriors · real outcomes", "p": proof_p, "g": proof_g},
        {"id": "features", "label": "What you get", "tag": "winning arm's signals", "p": feat_p, "g": feat_g},
        {"id": "offer", "label": "Offer", "tag": "served online · Gate-cleared", "p": offer_p, "g": offer_g},
        {"id": "category", "label": "Why us", "tag": "truth-bounded · measured lift", "p": cat_p, "g": cat_g},
    ]


def _build_optimizer(slug: str, persona_key: str, overlay: dict,
                     ip: str, industry: str, region: str) -> dict:
    from pipeline.personalization import demo_scenarios as DS
    from pipeline.personalization import demo_sim
    d = DEMOS[slug]
    p = _persona_or_first(slug, persona_key)
    sid = p["sid"]
    scen = DS.scenario(sid)
    m = demo_sim.build()
    sc = next((x for x in m["scenarios"] if x["id"] == sid), m["scenarios"][0])
    arms = sc["arms"]
    win_id = sc.get("learned_winner") or sc.get("winner")
    winner = next((a for a in arms if a["id"] == win_id), arms[0])
    win_var = next((v for v in scen.variants if v.id == win_id), None)
    blk = sc.get("blocked_arm")
    blk_var = DS.blocked_variant(scen)
    ind_key = industry or overlay.get("industry") or "technology"
    img = SC.image_for(ind_key)
    fill = lambda s: (s or "").replace("{brand}", _OPT_SITE)  # noqa: E731
    share = int(sc.get("winner_share", 0) * 100)
    n_blk = blk["selections"] if blk else 0
    sections = _opt_sections(scen, sc, win_var, blk_var, fill=fill)

    ungated_hero = {"eyebrow": "The arm that would win on engagement",
                    "headline": fill(blk_var.headline) if blk_var else "The arm that would win the click — and never ships.",
                    "sub": fill(blk_var.sub) if blk_var else "The highest-engagement variant, but it crosses the line the Gate holds.",
                    "cta": fill(blk_var.cta) if blk_var else "Show me", "image": img["url"], "attr": img}

    impact = _impact(sections, (len(win_var.data_used) if win_var else 1) + 1,
                     lift_label=f"{share}% of pulls on the proven winner",
                     lift_note="share of pulls the bandit converged on the Gate-cleared winner; lift is measured vs a random control, not asserted")

    arm_rows = [{"k": a["label"], "v": f"posterior {a['posterior_mean']}", "conf": "high" if a["id"] == win_id else None,
                 "meta": "learned winner" if a["id"] == win_id else f"{a.get('selections', 0)} pulls"} for a in arms]
    arm_rows.append({"k": (blk_var.label if blk_var else "the ungated arm"), "v": "excluded from the action pool",
                     "meta": f"selected {n_blk}× — the planted lie"})
    decision = [{"k": "Algorithm", "v": "Thompson sampling, per segment"},
                {"k": "Learned winner", "v": (win_var.label if win_var else winner["label"])},
                {"k": "Converged", "v": "yes" if sc.get("converged") else "approaching"}]
    assembly = [{"k": s["label"], "v": s["p"]["headline"], "meta": "from " + s["tag"]} for s in sections]
    prov = ([{"k": du.signal, "v": du.role, "meta": f"{du.policy} · {du.source_label}"} for du in win_var.data_used]
            if win_var else [{"k": "—", "v": "the winner's signals", "meta": "Gate-cleared"}])
    obs_sections = [
        {"title": "Arms — per-segment posteriors", "icon": "ph-chart-bar", "mode": True, "rows": arm_rows},
        {"title": "Decision — the bandit", "icon": "ph-strategy", "rows": decision},
        {"title": "Page assembly — block ← signal", "icon": "ph-stack", "rows": assembly},
        {"title": "Provenance — what the winner may say", "icon": "ph-seal-check", "rows": prov}]
    gate = [{"verdict": "ok", "line": a["label"], "why": f"Gate-cleared arm · posterior {a['posterior_mean']}"} for a in arms]
    gate.append({"verdict": "block", "line": (blk_var.label if blk_var else "the ungated arm"),
                 "why": f"unprovable overclaim — excluded from the action pool; selected {n_blk}×"})
    trace = [{"n": 1, "name": "Generate", "detail": f"{sc['label']} — per-segment A/B variants + the planted lie"},
             {"n": 2, "name": "Gate", "detail": "every variant verified; the lie is blocked"},
             {"n": 3, "name": "Action pool", "detail": "only Gate-cleared arms enter — the lie excluded by construction"},
             {"n": 4, "name": "Learn", "detail": f"Thompson sampling over real outcomes → “{win_var.label if win_var else winner['label']}”"},
             {"n": 5, "name": "Serve", "detail": f"the learned winner ({share}% of pulls); lift measured vs a random control"},
             {"n": 6, "name": "Drift", "detail": "a source change / legal hold re-verifies + pauses affected arms"}]
    return _rich_vm(d, site=_OPT_SITE, img=img, sections=sections, impact=impact, ungated_hero=ungated_hero,
                    obs_sections=obs_sections, gate=gate, trace=trace, personas=PERSONAS["optimizer"],
                    active_persona=p["key"], active_ip=ip, active_industry=industry or "", active_region=region or "",
                    ungated_note="an unprovable overclaim — structurally excluded")


def build_view(slug: str, *, det: dict | None = None, octx: dict | None = None,
               gate=None, library=None, persona: str = "", overlay: dict | None = None,
               ip: str = "", industry: str = "", region: str = "") -> dict:
    """Dispatch to the right engine and return the normalized rich view-model."""
    kind = DEMOS[slug].kind
    if kind == "firmographic":
        return _build_firmographic(slug, det or {}, octx or {})
    if kind == "known":
        return _build_known(slug, gate, library, persona, overlay or {}, ip, industry, region)
    return _build_optimizer(slug, persona, overlay or {}, ip, industry, region)
