"""Marketing/sales translation of the /dev decision page — for directors of marketing.

Deterministic transform of the `page` dict from GS.build_page() into plain-English
sections. No LLM, no extra state — same inputs as /dev.
"""
from __future__ import annotations

from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_gen as IG

# Real demo scale — used in impact framing.
X_TARGETING_TYPES = len({v["x_targeting_type"] for v in GS.AD_VARIANTS})
AD_VARIANT_COUNT = len(GS.AD_VARIANTS)
COPY_SLOT_COUNT = 11  # slots tracked in build_page copy_diff (hero through final CTA)

_AUDIENCE_LABELS = {
    "companies": "B2B hiring & upskilling leaders",
    "individuals": "Individual engineers (Challenger track)",
    "neutral": "Mixed intent — no strong segment signal yet",
}

_NETWORK_FRAMING = {
    "corporate": "Likely visiting from a corporate network — we lean toward Hire/Catalyst messaging.",
    "corporate (via VPN)": "Corporate network (possibly via VPN) — B2B hire/upskill framing.",
    "residential": "Residential connection — individual engineer / Challenger track is likelier.",
    "consumer ISP": "Consumer ISP — individual engineer / Challenger track is likelier.",
    "mobile": "Mobile connection — individual engineer / Challenger track is likelier.",
}

_ANON_SIGNAL = {
    0: "No reliable firmographic signal — we keep copy neutral and let the entry channel lead.",
    1: "Geographic hint only — we can reference their region in framing without naming them.",
    2: "Industry signal — we can tailor proof and headlines to their sector (never their company name).",
    3: "Strong firmographic signal — sector + region framing, still no creepy recitation.",
}


def _changed_slots(page: dict) -> list[dict]:
    return [d for d in page.get("copy_diff", []) if d.get("changed")]


def _slot_response(d: dict) -> str:
    """How copy addresses a barrier or segment — one line for marketers."""
    if not d.get("changed"):
        return "Uses the default site copy — no personalization needed for this slot."
    pol = d.get("policy", "")
    if pol == "say":
        return "Stated directly — this visitor gave us permission to say it (login, form, or work email)."
    if pol == "allude":
        return "Shaped by inferred context — message match without naming private details."
    return "Held back — inferred fact steers internally but never appears on the page."


def _executive_summary(page: dict) -> str:
    entry = page["entry"]
    ident = page.get("identity")
    ad = page.get("ad_variant")
    changed = len(_changed_slots(page))
    audience = page.get("audience", "neutral")

    parts: list[str] = []
    parts.append(
        f"For this visitor, we rebuilt the landing page from how they arrived"
        + (f" ({entry['channel_label'].lower()})" if entry else "")
        + f" and what we can infer anonymously."
    )

    if ad:
        parts.append(
            f"They clicked an X ad built for {ad['x_targeting_type'].lower()} — "
            f"so the hero, CTAs, and proof points message-match that ad promise "
            f"({ad['page']['h1_pre'].strip()}{ad['page']['h1_gold']})."
        )
    elif entry.get("channel") == "email":
        parts.append(
            "They came from a marketing email — we use retargeting warmth and, if identified, "
            "first-name welcome-back copy."
        )
    elif entry.get("channel") == "search":
        parts.append(
            "They found us via search — no campaign promise to honor, so copy stays intent-neutral "
            "unless CRM or IP adds context."
        )
    else:
        parts.append(
            "Direct visit — we rely on anonymous firmographic hints and any CRM data after login."
        )

    if ident:
        if ident.get("kind") == "cohort":
            parts.append(
                f"We know who they are ({ident['view']['name']}) — lifecycle stage, past behavior, "
                f"and declared intent reshape CTAs and social proof while respecting brand-safe boundaries."
            )
        else:
            co = (ident.get("resolved") or {}).get("company")
            parts.append(
                f"They logged in with a work email"
                + (f" — we can say “your team at {co}”" if co else "")
                + " and route them toward the right funnel."
            )
    else:
        parts.append(
            f"We route them toward {_AUDIENCE_LABELS.get(audience, audience)} "
            f"and personalized {changed} of {len(page.get('copy_diff', []))} copy slots."
        )

    return " ".join(parts[:4])


def _decision_bullets(page: dict) -> list[str]:
    """Five-bullet executive summary from trace — marketing language, not raw JSON."""
    entry = page["entry"]
    ad = page.get("ad_variant")
    ident = page.get("identity")
    objections = page.get("objections", {}).get("prioritized") or []
    changed = len(_changed_slots(page))
    bullets: list[str] = []

    bullets.append(
        f"Arrival: {entry['channel_label']}"
        + (f" · campaign “{entry.get('utm_campaign') or '—'}”" if entry.get("utm_campaign") else "")
        + " — we honor the click context before anything else."
    )

    net = page["det"].get("network_type") or "unknown"
    tier = page.get("tier", 0)
    bullets.append(
        f"Anonymous intelligence: {_ANON_SIGNAL.get(tier, _ANON_SIGNAL[0])} "
        f"(network: {net})."
    )

    if ad:
        bullets.append(
            f"Ad segment: {ad['x_targeting_type']} targeting "
            f"({ad['x_targeting_example']}) — full message match on hero, proof, and CTAs."
        )
    elif ident:
        bullets.append(
            f"Known lead: {ident.get('email', 'identified')} — CRM archetype drives section order and CTA emphasis."
        )
    else:
        bullets.append(
            f"Audience route: {_AUDIENCE_LABELS.get(page.get('audience', 'neutral'), page.get('audience'))}."
        )

    if objections:
        top = objections[0]
        bullets.append(
            f"Top conversion barrier: “{top['text']}” — copy and visual strategy address it in "
            f"{len(page.get('objections', {}).get('assignments') or [])} slot(s)."
        )
    else:
        bullets.append("No ranked objections fired — generic proof and CTAs ship.")

    bullets.append(
        f"Shipped experience: {changed} personalized copy slots + "
        f"{page.get('sections', {}).get('hero', {}).get('cta_primary', 'primary CTA')} as the lead action."
    )

    return bullets[:5]


def _ad_copy(ad: dict) -> dict:
    """Ad mockup fields live under ad['ad'] in the variant catalog."""
    return ad.get("ad") or ad


def _visitor_journey(page: dict) -> list[dict]:
    steps: list[dict] = []
    entry = page["entry"]
    steps.append({
        "phase": "How they arrived",
        "headline": entry["channel_label"],
        "detail": entry.get("why", ""),
        "signals": [s for s in entry.get("signals", []) if s.get("value") not in ("—", "", None)],
    })

    det = page["det"]
    net = det.get("network_type") or "private / unreachable"
    tier = page.get("tier", 0)
    anon_detail = _NETWORK_FRAMING.get(net, _ANON_SIGNAL.get(tier, _ANON_SIGNAL[0]))
    if det.get("region") or det.get("industry"):
        hints = []
        if det.get("region"):
            hints.append(f"region: {det['region']}")
        if det.get("industry"):
            hints.append(f"sector hint: {det['industry']}")
        anon_detail += " · " + " · ".join(hints)
    steps.append({
        "phase": "What we know anonymously",
        "headline": "Firmographic & network hints (never creepy)",
        "detail": anon_detail,
        "signals": [],
    })

    ad = page.get("ad_variant")
    if ad:
        ac = _ad_copy(ad)
        steps.append({
            "phase": "Audience segment & ad promise",
            "headline": ad["x_targeting_type"],
            "detail": f"Ad hook: “{ac.get('trigger', '')}” → landing message-match to "
                      f"“{ad['page']['h1_pre']}{ad['page']['h1_gold']}”.",
            "signals": [{"label": "X targeting example", "value": ad["x_targeting_example"]}],
        })
    else:
        steps.append({
            "phase": "Segment routing",
            "headline": _AUDIENCE_LABELS.get(page.get("audience", "neutral"), page["audience"]),
            "detail": page.get("audience_rule", page.get("audience_why", "")),
            "signals": [],
        })

    changed = _changed_slots(page)
    steps.append({
        "phase": "Personalized experience",
        "headline": f"{len(changed)} copy slots tailored · section order optimized",
        "detail": "Same page structure for everyone — only headlines, CTAs, proof emphasis, "
                  "and visual mood change. No fabricated claims.",
        "signals": [],
    })
    return steps


def _campaign_context(page: dict) -> dict | None:
    ad = page.get("ad_variant")
    if not ad:
        return None
    vp = ad["page"]
    ac = _ad_copy(ad)
    return {
        "targeting_type": ad["x_targeting_type"],
        "targeting_example": ad["x_targeting_example"],
        "audience_fit": ad.get("audience_fit", ""),
        "ad_hook": ac.get("trigger", ""),
        "ad_body": ac.get("body", ""),
        "ad_proof": ac.get("proof", ""),
        "ad_cta": ac.get("cta_label", ""),
        "landing_headline": vp["h1_pre"] + vp["h1_gold"],
        "landing_sub": vp["sub"],
        "message_match_strategy": (
            "The landing page continues the ad conversation — headline, eyebrow, proof block, "
            "and primary CTA all echo what they clicked so bounce from message mismatch stays low."
        ),
        "variant_id": ad["variant_id"],
        "utm_campaign": ad["utm_campaign"],
    }


def _barriers(page: dict) -> list[dict]:
    out: list[dict] = []
    assignments = {a["rank"]: a for a in page.get("objections", {}).get("assignments") or []}
    for o in page.get("objections", {}).get("prioritized") or []:
        a = assignments.get(o["rank"])
        slot_label = a["slot"].replace("_", " ") if a else "—"
        response = "Addressed in copy" if a else "Ranked for strategy — generic copy ships"
        if a and a["slot"] == "hero_sub":
            response = "Hero subhead reframed to counter this objection directly."
        elif a and a["slot"] == "challenger_body":
            response = "Challenger callout warmed with social proof / loss framing."
        elif a and a["slot"] == "final_cta":
            response = "Bottom CTA uses urgency or finish-what-you-started framing."
        out.append({
            "rank": o["rank"],
            "barrier": o["text"],
            "why_now": o.get("why_prioritized", ""),
            "copy_response": response,
            "slot": slot_label,
        })
    return out


def _personalized_experience(page: dict) -> dict:
    hero = page.get("sections", {}).get("hero", {})
    cta = page.get("sections", {}).get("cta", {})
    compare = page.get("sections", {}).get("compare", {})
    hi = page.get("hero_image") or {}
    hid = hi.get("dev") or IG.hero_image_dev_panel(hi)
    conv = hid.get("conversion") or {}

    slots = []
    for d in page.get("copy_diff", []):
        if not d.get("changed"):
            continue
        slots.append({
            "label": d["label"],
            "generic": (d.get("generic") or "—")[:220],
            "personalized": (d.get("shipped") or "—")[:220],
            "response": _slot_response(d),
        })

    visual = {
        "goal": conv.get("goal") or "Support the primary conversion action",
        "technique": conv.get("sales_technique") or "—",
        "drives_action": conv.get("drives_action") or hero.get("cta_primary", ""),
        "mood": (hid.get("prompt") or {}).get("mood") or "Professional, high-trust",
        "metaphor": (hid.get("prompt") or {}).get("visual_metaphor") or "—",
        "intent_summary": "",
    }
    intents = (hid.get("intent_selection") or {}).get("intents") or []
    primary = next((i for i in intents if i.get("primary")), intents[0] if intents else None)
    if primary:
        visual["intent_summary"] = (
            f"Background visual strategy: {primary['intent_id'].replace('_', ' ')} — "
            f"{primary.get('why', 'reinforces the hero CTA emotionally')}."
        )

    return {
        "hero_headline": (hero.get("h1_pre", "") + hero.get("h1_gold", "")).strip(),
        "hero_sub": hero.get("sub", ""),
        "hero_eyebrow": hero.get("eyebrow", ""),
        "cta_primary": hero.get("cta_primary", ""),
        "cta_secondary": hero.get("cta_secondary", ""),
        "final_cta_heading": cta.get("heading", ""),
        "final_cta_sub": cta.get("sub", ""),
        "compare_emphasis": compare.get("emphasis") or "equal weight",
        "section_order": page.get("order", []),
        "slots": slots,
        "visual": visual,
        "hero_image_url": hi.get("url"),
    }


def _lead_intelligence(page: dict) -> dict | None:
    ident = page.get("identity")
    if not ident:
        return None
    if ident.get("kind") == "cohort":
        v = ident["view"]
        hs = v["hubspot"]
        return {
            "kind": "crm",
            "name": v["name"],
            "email": v["email"],
            "lifecycle": hs.get("lifecycle", "—"),
            "lead_score": hs.get("lead_score"),
            "visits": hs.get("visits"),
            "top_pages": hs.get("top_pages") or [],
            "abandoned": hs.get("abandoned"),
            "declared_goal": v.get("declared", {}).get("goal"),
            "title": v["linkedin"].get("title"),
            "company_inferred": v["linkedin"].get("company"),
            "archetype": ident["archetype"]["label"],
            "archetype_reason": ident["archetype"]["reason"],
            "recommended_cta": ident["archetype"].get("cta", ""),
            "segments": [
                s["label"]
                for d in ident.get("segments", {}).values()
                for s in d.get("segments", [])
            ],
            "sales_handoff": _sales_handoff_cohort(v, ident["archetype"]),
        }
    if ident.get("kind") == "resolved":
        r = ident["resolved"]
        return {
            "kind": "domain",
            "email": ident["email"],
            "company": r.get("company"),
            "sales_handoff": f"Work-email login — treat as inbound from {r.get('company') or 'their org'}. "
                             "No full CRM record in demo; first-party domain is say-level.",
        }
    return None


def _sales_handoff_cohort(v: dict, arch: dict) -> str:
    hs = v["hubspot"]
    if hs.get("abandoned"):
        return "High-intent abandon — retarget with finish-your-application creative; avoid shaming copy."
    if hs.get("lifecycle") in ("customer", "past customer"):
        return "Past customer — upsell/cross-sell warmth; emphasize continuity, not cold acquisition."
    if v.get("declared", {}).get("goal"):
        return f"Declared goal on file — lead with “you told us you want to {v['declared']['goal']}” in email nurtures."
    return f"Archetype {arch['label']} — emphasize {arch.get('cta', 'primary CTA')} in sales follow-up."


def _privacy_framing(page: dict) -> dict:
    held: list[str] = []
    steered: list[str] = []
    said: list[str] = []

    for d in page.get("copy_diff", []):
        if d.get("blocked_say"):
            held.append(f"We never say: “{d['blocked_say'][:120]}…”")
        pol = d.get("policy")
        if pol == "hold":
            held.append(f"{d['label']}: inferred fact held — never shown.")
        elif pol == "allude" and d.get("changed"):
            steered.append(f"{d['label']}: shaped by context, not recited.")

    for b in page.get("objections", {}).get("blocked") or []:
        if b.get("blocked_say"):
            held.append(f"Objection reframe blocked: “{b['blocked_say'][:100]}…”")

    ad = page.get("ad_variant")
    if ad and ad.get("hold_note"):
        held.append(ad["hold_note"])

    ident = page.get("identity")
    if ident and ident.get("kind") == "cohort":
        said.append("First name & declared form answers — stated openly when logged in.")
        steered.append("Employer/title from enrichment — steers tone, never quoted on page.")
        held.append("Modeled income & precise geo — never displayed (brand safety).")
    elif ident and ident.get("kind") == "resolved":
        said.append("Company name from work email domain — fair game to say aloud.")

    return {
        "headline": "What we say out loud vs. what we use to steer",
        "said": said or ["Only first-party declared facts when the visitor identifies themselves."],
        "steered": steered or ["Anonymous firmographics and ad context shape copy without naming the visitor."],
        "held": held or ["No hold-tier facts for this visitor — nothing blocked from shipping."],
        "trust_frame": "We never mention their company name from IP alone, never recite behavioral "
                       "micro-details (“you bounced at step 3”), and never surface modeled demographics.",
    }


def _recommended_actions(page: dict) -> list[str]:
    entry = page["entry"]
    ad = page.get("ad_variant")
    ident = page.get("identity")
    actions: list[str] = []

    if ad:
        actions.append(
            f"Run A/B tests across 3+ X targeting types (you have {AD_VARIANT_COUNT} catalogued) "
            f"with UTMs like utm_campaign={ad['utm_campaign']}&utm_content={ad['variant_id']} — "
            "compare landing conversion by segment."
        )
        actions.append(
            "Audit message match: ad mockup copy ↔ landing hero ↔ email follow-up should use the same headline promise."
        )
    elif entry.get("channel") == "email":
        actions.append(
            "Segment email nurtures by lifecycle (HubSpot) — warm subject lines for identified clicks, "
            "generic proof for cold list."
        )
    else:
        actions.append(
            "Build entry-channel dashboards: paid vs search vs direct — personalization depth differs by arrival."
        )

    if ident:
        actions.append(
            "Sync CRM lifecycle to ad retargeting pools — abandoned applicants get finish-framing; "
            "customers get upsell warmth."
        )
    else:
        actions.append(
            "Test anonymous firmographic copy (industry/region framing) vs fully generic — "
            "measure lift without increasing creepiness."
        )

    actions.append(
        f"Scale impact: {AD_VARIANT_COUNT} ad variants × {COPY_SLOT_COUNT}+ personalized LP slots = "
        f"message match at scale across {X_TARGETING_TYPES} X targeting types."
    )
    return actions[:4]


def _impact_framing() -> dict:
    return {
        "variants": AD_VARIANT_COUNT,
        "targeting_types": X_TARGETING_TYPES,
        "copy_slots": COPY_SLOT_COUNT,
        "headline": f"{AD_VARIANT_COUNT} ad variants × {COPY_SLOT_COUNT}+ personalized landing slots",
        "sub": f"Covers all {X_TARGETING_TYPES} X Ads Manager targeting types in this demo — "
               "each click gets a matched hero, CTA, proof emphasis, objection handling, and visual mood.",
    }


def _technical_details(page: dict) -> dict:
    return {
        "tier": page.get("tier"),
        "tier_label": page.get("tier_label"),
        "audience_route": page.get("audience_route"),
        "trace_stages": [t["stage"] for t in page.get("trace", [])],
        "personalized_count": len(_changed_slots(page)),
        "total_slots": len(page.get("copy_diff", [])),
    }


def build_business_dev_view(page: dict) -> dict:
    """Transform build_page() output into marketing-friendly sections."""
    return {
        "executive_summary": _executive_summary(page),
        "decision_bullets": _decision_bullets(page),
        "visitor_journey": _visitor_journey(page),
        "campaign": _campaign_context(page),
        "barriers": _barriers(page),
        "experience": _personalized_experience(page),
        "lead": _lead_intelligence(page),
        "privacy": _privacy_framing(page),
        "recommended_actions": _recommended_actions(page),
        "impact": _impact_framing(),
        "technical": _technical_details(page),
    }
