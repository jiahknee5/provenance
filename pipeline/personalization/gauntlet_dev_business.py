"""Marketing decision log for /dev/business — campaign ops view for practitioner marketers.

Deterministic transform of the `page` dict from GS.build_page() into decision rows
a marketer can audit: arrival, segment, objections, copy slots, visual, CRM steering.
No LLM, no extra state — same inputs as /dev.
"""
from __future__ import annotations

from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_gen as IG

_AUDIENCE_LABELS = {
    "companies": "B2B hiring & upskilling leaders",
    "individuals": "Individual engineers (Challenger track)",
    "neutral": "Mixed intent — no strong segment signal yet",
}

_SEGMENT_PERSONAS = {
    "CTO": "CTO / VP Engineering hire track",
    "Engineer": "Senior engineer Challenger track",
    "HR/L&D": "HR / L&D Catalyst upskill track",
    "cross-audience": "Cross-audience — message match only",
}

_NETWORK_READ = {
    "corporate": "Corporate IP → B2B hire / Catalyst track is likelier",
    "corporate (via VPN)": "Corporate network (possibly VPN) → B2B hire framing",
    "residential": "Residential connection → individual engineer / Challenger track",
    "consumer ISP": "Consumer ISP → individual engineer / Challenger track",
    "mobile": "Mobile connection → individual engineer / Challenger track",
}

_FIRMOGRAPHIC_READ = {
    0: "No firmographic hint — copy stays neutral; entry channel leads",
    1: "Geo hint only — can reference region in framing, never name them",
    2: "Industry signal — tailor proof and headlines to sector (never company name)",
    3: "Strong firmographic signal — sector + region framing, still no creepy recitation",
}

_SLOT_LABELS = {
    "hero_eyebrow": "Hero eyebrow",
    "hero_headline": "Hero headline",
    "hero_sub": "Hero subhead",
    "cta_primary": "Primary CTA",
    "cta_secondary": "Secondary CTA",
    "prove_intro": "Proof block intro",
    "challenger_body": "Challenger callout",
    "compare_emphasis": "Comparison table emphasis",
    "numbers_order": "Stats emphasis order",
    "final_cta": "Final CTA block",
}


def _changed_slots(page: dict) -> list[dict]:
    return [d for d in page.get("copy_diff", []) if d.get("changed")]


def _ad_copy(ad: dict) -> dict:
    return ad.get("ad") or ad


def _marketer_reason(d: dict) -> str:
    """Translate slot source/why into campaign-ops language."""
    src = (d.get("source") or "—").strip()
    why = (d.get("why") or "").strip()
    parts: list[str] = []
    if src and src != "—":
        if "ad variant" in src.lower():
            parts.append(f"Campaign match ({src})")
        elif "reverse-ip" in src.lower() or "firmographic" in src.lower():
            parts.append("Firmographic hint shapes copy — never recited")
        elif "hubspot" in src.lower() or "crm" in src.lower():
            parts.append(f"CRM signal ({src})")
        elif "objection" in src.lower():
            parts.append(f"Objection reframe ({src})")
        elif "identity" in src.lower() or "work-email" in src.lower():
            parts.append(f"First-party identity ({src})")
        elif "audience" in src.lower():
            parts.append(f"Segment routing ({src})")
        else:
            parts.append(src)
    if why:
        parts.append(why)
    if not parts:
        return "Default site copy — no signal triggered a change"
    return " · ".join(parts)


def _slot_decision(d: dict) -> str:
    if not d.get("changed"):
        return "Decision: ship default — no personalization signal for this slot"
    pol = d.get("policy", "")
    reason = _marketer_reason(d)
    if pol == "say":
        return f"Decision: say it out loud — {reason}"
    if pol == "allude":
        return f"Decision: steer with context — {reason}"
    return f"Decision: hold inferred fact — {reason}"


def _arrival_attribution(page: dict) -> dict:
    entry = page["entry"]
    ad = page.get("ad_variant")
    rows: list[dict] = [
        {"label": "Channel", "value": entry["channel_label"], "note": entry.get("why", "")},
        {"label": "utm_source", "value": entry.get("utm_source") or "—"},
        {"label": "utm_medium", "value": entry.get("utm_medium") or "—"},
        {"label": "utm_campaign", "value": entry.get("utm_campaign") or "—"},
        {"label": "utm_content", "value": entry.get("utm_content") or "—"},
        {"label": "Entry rule fired", "value": entry.get("rule", "—"), "note": "How we classified the click"},
    ]
    if ad:
        ac = _ad_copy(ad)
        rows.extend([
            {"label": "X targeting type", "value": ad["x_targeting_type"],
             "note": ad["x_targeting_example"]},
            {"label": "Ad variant", "value": ad["variant_id"],
             "note": f"utm_campaign={ad['utm_campaign']}"},
            {"label": "Ad hook (clicked)", "value": f"“{ac.get('trigger', '')}”"},
            {"label": "Ad body", "value": ac.get("body", "—")},
            {"label": "Ad CTA", "value": ac.get("cta_label", "—")},
            {"label": "Message-match rule",
             "value": f"Hero must echo ad promise: “{ad['page']['h1_pre']}{ad['page']['h1_gold']}”",
             "note": "Landing headline, eyebrow, proof, and primary CTA continue the ad conversation"},
        ])
    elif entry.get("channel") == "email":
        rows.append({"label": "Message-match rule",
                     "value": "Email retarget — warm welcome-back if identified, generic proof if cold",
                     "note": entry.get("why", "")})
    elif entry.get("channel") == "search":
        rows.append({"label": "Message-match rule",
                     "value": "Search arrival — no campaign promise; copy stays intent-neutral",
                     "note": entry.get("why", "")})
    else:
        rows.append({"label": "Message-match rule",
                     "value": "Direct visit — IP firmographics and CRM (if any) steer copy",
                     "note": entry.get("why", "")})

    decision = f"Decision: classify as {entry['channel_label'].lower()}"
    if ad:
        decision += f" → message-match {ad['x_targeting_type'].lower()} ad variant {ad['variant_id']}"
    elif entry.get("utm_campaign"):
        decision += f" → honor utm_campaign={entry['utm_campaign']}"
    else:
        decision += " → no ad promise to match"

    return {"channel": entry["channel_label"], "decision": decision, "rows": rows}


def _audience_read(page: dict) -> dict:
    det = page["det"]
    ad = page.get("ad_variant")
    audience = page.get("audience", "neutral")
    tier = page.get("tier", 0)
    net = det.get("network_type") or "unknown"

    if ad:
        segment = _SEGMENT_PERSONAS.get(ad.get("audience_fit", ""), ad.get("audience_fit_label", ""))
        segment_note = f"Ad audience fit: {ad.get('audience_fit_label', '—')}"
    else:
        segment = _AUDIENCE_LABELS.get(audience, audience)
        segment_note = page.get("audience_rule") or page.get("audience_why", "")

    signals: list[dict] = []
    net_read = _NETWORK_READ.get(net)
    if net_read:
        signals.append({"label": "Network read", "value": net_read})
    elif net not in ("unknown", "private / unreachable", ""):
        signals.append({"label": "Network read", "value": f"{net} connection"})

    firmo = _FIRMOGRAPHIC_READ.get(tier, _FIRMOGRAPHIC_READ[0])
    signals.append({"label": "Anonymous signal", "value": firmo})
    if det.get("industry"):
        signals.append({"label": "Firmographic hint", "value": f"Sector: {det['industry']}"})
    if det.get("region"):
        signals.append({"label": "Firmographic hint", "value": f"Region: {det['region']}"})

    ident = page.get("identity")
    if ident:
        if ident.get("kind") == "cohort":
            arch = ident.get("archetype", {})
            signals.append({"label": "CRM segment",
                              "value": f"{arch.get('label', 'Known lead')} — {arch.get('reason', '')}"})
        elif ident.get("kind") == "resolved":
            co = (ident.get("resolved") or {}).get("company")
            signals.append({"label": "Login signal",
                              "value": f"Work email" + (f" from {co}" if co else "")})

    route = _AUDIENCE_LABELS.get(audience, audience)
    decision = f"Decision: route to {route}"
    if ad:
        decision += f" — ad targets {_SEGMENT_PERSONAS.get(ad.get('audience_fit', ''), ad['x_targeting_type'])}"
    elif tier >= 2 and det.get("industry"):
        decision += f" — industry hint ({det['industry']}) steers proof and framing"
    elif net in ("corporate", "corporate (via VPN)"):
        decision += " — corporate network leans B2B hire track"

    return {
        "segment": segment,
        "segment_note": segment_note,
        "decision": decision,
        "signals": signals,
    }


def _shipped_reframe(page: dict, slot: str, rank: int) -> str:
    """Pull the actual copy text that answered an objection."""
    sections = page.get("sections", {})
    hero = sections.get("hero", {})
    challenger = sections.get("challenger", {})
    cta = sections.get("cta", {})
    prove = sections.get("prove", {})

    if slot == "hero_sub":
        return hero.get("sub", "—")
    if slot == "challenger_body":
        return challenger.get("body", "—")
    if slot == "final_cta":
        return f"{cta.get('heading', '')} · {cta.get('sub', '')}"
    if slot.startswith("prove_card_"):
        try:
            idx = int(slot.split("_")[-1])
            cards = prove.get("cards") or []
            if 0 <= idx < len(cards):
                title, body = cards[idx]
                return f"{title}: {body}"
        except (ValueError, TypeError):
            pass
    if slot == "compare_row":
        compare = sections.get("compare", {})
        row = compare.get("row_emphasis")
        return f"Highlighted comparison row: {row}" if row else "Comparison row emphasis applied"
    if slot == "compare_emphasis":
        emph = sections.get("compare", {}).get("emphasis")
        return f"Column emphasis: {emph}" if emph else "—"

    for row in page.get("objections", {}).get("prioritized") or []:
        if row.get("rank") == rank:
            obj = row.get("objection") or {}
            rf = obj.get("reframe", {})
            for key in ("hero_sub", "challenger_body", "final_cta_sub"):
                if rf.get(key):
                    return rf[key]
    return "—"


def _objection_stack(page: dict) -> list[dict]:
    out: list[dict] = []
    assignments = {a["rank"]: a for a in page.get("objections", {}).get("assignments") or []}
    for o in page.get("objections", {}).get("prioritized") or []:
        a = assignments.get(o["rank"])
        slot_key = a["slot"] if a else None
        slot_label = _SLOT_LABELS.get(slot_key, slot_key.replace("_", " ") if slot_key else "—")
        reframe = _shipped_reframe(page, slot_key, o["rank"]) if slot_key else "—"
        decision = (
            f"Decision: answer objection #{o['rank']} in {slot_label}"
            if a else f"Decision: rank objection #{o['rank']} for strategy — generic copy ships"
        )
        if a:
            decision += f" — {o.get('why_prioritized', '')}"
        out.append({
            "rank": o["rank"],
            "barrier": o["text"],
            "why_now": o.get("why_prioritized", ""),
            "slot": slot_label,
            "reframe_text": reframe,
            "decision": decision,
        })
    return out


def _copy_decisions(page: dict) -> list[dict]:
    out: list[dict] = []
    for d in page.get("copy_diff", []):
        out.append({
            "slot": d.get("label") or d.get("slot", "—"),
            "generic": (d.get("generic") or "—")[:280],
            "shipped": (d.get("shipped") or "—")[:280],
            "changed": bool(d.get("changed")),
            "decision": _slot_decision(d),
            "reason": _marketer_reason(d),
        })
    return out


def _visual_decision(page: dict) -> dict:
    hero = page.get("sections", {}).get("hero", {})
    hi = page.get("hero_image") or {}
    hid = hi.get("dev") or IG.hero_image_dev_panel(hi)
    conv = hid.get("conversion") or {}
    prompt = hid.get("prompt") or {}
    intents = (hid.get("intent_selection") or {}).get("intents") or []
    primary = next((i for i in intents if i.get("primary")), intents[0] if intents else None)

    intent_id = primary["intent_id"].replace("_", " ") if primary else "default gradient"
    intent_why = primary.get("why", "reinforces the hero CTA emotionally") if primary else "—"
    mood = prompt.get("mood") or "Professional, high-trust"
    metaphor = prompt.get("visual_metaphor") or "—"
    technique = conv.get("sales_technique") or "—"
    drives = conv.get("drives_action") or hero.get("cta_primary", "")

    decision = (
        f"Decision: hero background uses {intent_id} visual strategy"
        f" — paired with “{drives}” CTA"
    )

    return {
        "decision": decision,
        "intent": intent_id,
        "intent_why": intent_why,
        "mood": mood,
        "metaphor": metaphor,
        "technique": technique,
        "paired_cta": drives,
        "goal": conv.get("goal") or "Support the primary conversion action",
        "hero_image_url": hi.get("url"),
    }


def _lead_context(page: dict) -> dict | None:
    ident = page.get("identity")
    if not ident:
        return None

    steering: list[str] = []
    if ident.get("kind") == "cohort":
        v = ident["view"]
        hs = v["hubspot"]
        if v.get("declared", {}).get("goal"):
            steering.append(
                f"Declared goal “{v['declared']['goal']}” → hero sub can say it (first-party)"
            )
        if hs.get("abandoned"):
            steering.append(
                f"Abandoned {hs['abandoned']} → final CTA uses finish-what-you-started framing"
            )
        if hs.get("lifecycle") in ("customer", "past customer"):
            steering.append("Past customer lifecycle → welcome-back warmth, not cold acquisition")
        arch = ident.get("archetype", {})
        if arch.get("cta"):
            steering.append(f"Archetype {arch['label']} → recommended CTA: {arch['cta']}")
        if ident.get("first"):
            steering.append(f"First name available → eyebrow says “Welcome back, {ident['first']}”")

        return {
            "kind": "crm",
            "name": v["name"],
            "email": v["email"],
            "lifecycle": hs.get("lifecycle", "—"),
            "lead_score": hs.get("lead_score"),
            "visits": hs.get("visits"),
            "abandoned": hs.get("abandoned"),
            "declared_goal": v.get("declared", {}).get("goal"),
            "archetype": arch.get("label", "—"),
            "segments": [
                s["label"]
                for d in ident.get("segments", {}).values()
                for s in d.get("segments", [])
            ],
            "copy_steering": steering or ["CRM record present — archetype and lifecycle steer CTA emphasis"],
        }

    if ident.get("kind") == "resolved":
        r = ident["resolved"]
        co = r.get("company")
        if co:
            steering.append(f"Work-email domain → eyebrow can say “For your team at {co}”")
        return {
            "kind": "domain",
            "email": ident["email"],
            "company": co,
            "copy_steering": steering or ["Work-email login — first-party domain is fair to say"],
        }
    return None


def _steering_vs_saying(page: dict) -> dict:
    held: list[str] = []
    steered: list[str] = []
    said: list[str] = []

    for d in page.get("copy_diff", []):
        if d.get("blocked_say"):
            held.append(f"Never say: “{d['blocked_say'][:120]}…”")
        pol = d.get("policy")
        if pol == "hold":
            held.append(f"{d['label']}: inferred fact held — never shown on page")
        elif pol == "allude" and d.get("changed"):
            steered.append(f"{d['label']}: shaped by context, not recited")

    for b in page.get("objections", {}).get("blocked") or []:
        if b.get("blocked_say"):
            held.append(f"Objection reframe blocked: “{b['blocked_say'][:100]}…”")

    ad = page.get("ad_variant")
    if ad and ad.get("hold_note"):
        held.append(ad["hold_note"])

    ident = page.get("identity")
    if ident and ident.get("kind") == "cohort":
        said.append("First name & declared form answers — stated when logged in")
        steered.append("Employer/title from enrichment — steers tone, never quoted on page")
        held.append("Modeled income & precise geo — never displayed")
    elif ident and ident.get("kind") == "resolved":
        said.append("Company name from work email domain — fair game to say aloud")

    return {
        "said": said or ["Only first-party declared facts when the visitor identifies themselves"],
        "steered": steered or ["Anonymous firmographics and ad context shape copy without naming the visitor"],
        "held": held or ["No blocked facts for this visitor"],
        "rules": [
            "We steer on industry and segment — we never name their company from IP alone",
            "We never recite behavioral micro-details (“you bounced at step 3”)",
            "Ad targeting demographics (age/gender) steer internally — never appear on page",
        ],
    }


def build_business_dev_view(page: dict) -> dict:
    """Transform build_page() output into marketer decision-log sections."""
    return {
        "arrival": _arrival_attribution(page),
        "audience_read": _audience_read(page),
        "objections": _objection_stack(page),
        "copy_decisions": _copy_decisions(page),
        "visual": _visual_decision(page),
        "lead": _lead_context(page),
        "steering": _steering_vs_saying(page),
        "changed_count": len(_changed_slots(page)),
        "total_slots": len(page.get("copy_diff", [])),
    }
