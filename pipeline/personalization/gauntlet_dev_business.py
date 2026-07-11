"""Marketer console for /dev/business — review-and-customize surface for marketers.

Deterministic transform of the `page` dict from GS.build_page() plus the tenant
configs (rules/gauntlet_image.yaml, rules/gauntlet_prebuild.yaml) into the console
view: overview, workflow tree, incoming data, decisions, copy, images, guardrails,
delivery. No LLM, no extra state, no server-side writes — same inputs as /dev;
"customization" is staged config diffs rendered client-side.
"""
from __future__ import annotations

from pipeline.personalization import design_prompts as DP
from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II
from pipeline.personalization import prebuild as PB

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
    tier = hid.get("tier") or {}
    intents = (hid.get("intent_selection") or {}).get("intents") or []
    primary = next((i for i in intents if i.get("primary")), intents[0] if intents else None)

    intent_id = primary["intent_id"].replace("_", " ") if primary else "default gradient"
    intent_why = primary.get("why", "reinforces the hero CTA emotionally") if primary else "—"
    mood = prompt.get("mood") or "Professional, high-trust"
    metaphor = prompt.get("visual_metaphor") or "—"
    technique = conv.get("sales_technique") or "—"
    drives = conv.get("drives_action") or hero.get("cta_primary", "")

    ad = page.get("ad_variant") or {}
    ad_label = ad.get("label") or ad.get("id") or "standard"
    tier_mode = tier.get("mode", "base_only")

    if tier_mode == "base_only":
        tier_summary = f"Used standard {ad_label} visual — segment pre-cache, no extra adjustments"
    elif tier_mode == "base+delta":
        signals = tier.get("delta_signals") or []
        friendly = []
        for s in signals:
            if s.startswith("objection:"):
                friendly.append(s.split(":", 1)[1].replace("_", " ") + " objection")
            elif s.startswith("industry:"):
                friendly.append(s.split(":", 1)[1] + " industry")
            elif s.startswith("region:"):
                friendly.append(s.split(":", 1)[1] + " region")
            elif s.startswith("archetype:"):
                friendly.append("CRM archetype")
        adj = " + ".join(friendly) if friendly else "personalization signals"
        tier_summary = f"Adjusted for: {adj}"
    else:
        tier_summary = tier.get("label") or "Segment base visual"

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
        "tier_summary": tier_summary,
        "tier_mode": tier_mode,
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


# --------------------------------------------------------------------------- #
# Console view — workflow tree, incoming data, decisions, images, guardrails,
# delivery. Pure/deterministic functions of the page dict + config files.
# --------------------------------------------------------------------------- #
_POLICY_WORD = {"say": "say", "allude": "steer", "hold": "hold", "observed": "observed"}

# process_map stage id → (marketer title, the question the stage answers)
_WF_STAGES = {
    "entry": ("Arrival channel", "How did they get here?"),
    "advariant": ("Ad promise match", "Which campaign promise must the page keep?"),
    "ip": ("Network read", "What does the connection imply?"),
    "tier": ("Confidence gate", "How much is the visit allowed to shape?"),
    "identity": ("Identity", "Do we know who this is?"),
    "archetype": ("CRM persona", "Which persona steers emphasis?"),
    "audience": ("Audience routing", "Which segment does the page speak to?"),
    "objections": ("Objection ranking", "What's most likely holding them back?"),
    "policy": ("Say / steer / hold gate", "What may the page actually say?"),
    "compose": ("Page assembly", "What order do the sections ship in?"),
    "heroimg": ("Hero image", "Which visual strategy backs the headline?"),
    "imgsurfaces": ("Image surfaces", "Which images resolved for this visit?"),
}

_IMAGE_SURFACE_ORDER = ["hero", "og"]


def _pol_word(policy: str | None) -> str | None:
    return _POLICY_WORD.get(policy, policy) if policy else None


def _workflow(page: dict, pmap: dict) -> list[dict]:
    """The whole request as a vertical decision tree — every branch visible,
    the taken path highlighted, skipped stages dimmed. Marketer titles."""
    out = []
    for s in pmap["stages"]:
        title, question = _WF_STAGES.get(s["id"], (s["title"], ""))
        outcome = s["output"]
        if s["id"] == "tier":  # rephrase "tier N · label" in console vocabulary
            outcome = f"confidence {page['tier']} · {page['tier_label']}"
        out.append({
            "id": s["id"], "title": title, "question": question,
            "branches": s["branches"], "outcome": outcome, "why": s["why"],
            "skipped": s["skipped"], "skip_reason": s["skip_reason"],
        })
    # After compose: branch showing each image surface outcome for this visit.
    surfaces = page.get("image_surfaces") or {"hero": page.get("hero_image")}
    surface_branches = []
    surface_outcomes = []
    for sid in _IMAGE_SURFACE_ORDER:
        img = surfaces.get(sid)
        if not img:
            continue
        spec = IG.surface_spec(sid)
        src = ((img.get("receipt") or {}).get("source") or "gradient")
        intent = ((img.get("receipt") or {}).get("intent_id") or "—").replace("_", " ")
        surface_branches.append({"label": spec["label"], "taken": True})
        surface_outcomes.append(f"{spec['label'].split(' / ')[0]} → {src} · {intent}")
    if surface_branches:
        out.append({
            "id": "imgsurfaces", "title": "Image surfaces", "question": "Which images resolved?",
            "branches": surface_branches,
            "outcome": " · ".join(surface_outcomes),
            "why": "Each surface shares the intent stack but gets its own prompt shape, cache key, and load policy.",
            "skipped": False, "skip_reason": "",
        })
    return out


def _signals_in(page: dict) -> list[dict]:
    """Clay-style table of every incoming signal: value, source/vendor, policy."""
    rows = []
    for r in page.get("ledger", []):
        pol = r.get("policy", "observed")
        rows.append({
            "label": r.get("label", "—"), "value": r.get("value", "—"),
            "source": r.get("source", "—"), "vendor": r.get("vendor", "—"),
            "policy": _pol_word(pol),
        })
    return rows


def _decision_cards(page: dict, pmap: dict) -> list[dict]:
    """Per-decision cards: audience routing rungs, objection ranking, confidence gate."""
    by_id = {s["id"]: s for s in pmap["stages"]}
    cards: list[dict] = []

    aud = by_id.get("audience")
    if aud:
        cards.append({
            "id": "audience", "title": "Audience read",
            "subtitle": "Precedence: ad variant > campaign intent > CRM > work email > network",
            "branches": aud["branches"], "outcome": aud["output"], "why": aud["why"],
            "rows": [{"label": d["k"], "value": d["v"], "fired": d.get("fired", False),
                      "policy": _pol_word(d.get("pol"))} for d in aud["detail"]],
        })

    pri = page.get("objections", {}).get("prioritized") or []
    assignments = {a["rank"]: a for a in page.get("objections", {}).get("assignments") or []}
    obj_rows = []
    for o in pri:
        a = assignments.get(o["rank"])
        obj_rows.append({
            "label": f"#{o['rank']} — score {o['score']}",
            "value": f"“{o['text']}” · signals: {', '.join(o.get('signal_source') or [])}"
                     + (f" · answered in {_SLOT_LABELS.get(a['slot'], a['slot'])}" if a else " · ranked for strategy only"),
            "fired": True, "policy": "steer",
        })
    for b in page.get("objections", {}).get("blocked") or []:
        obj_rows.append({"label": f"blocked · {b['objection_id']}",
                         "value": f"“{b.get('blocked_say', '')}”", "fired": False, "policy": "hold"})
    obj = by_id.get("objections")
    cards.append({
        "id": "objections", "title": "Objection stack",
        "subtitle": "Signals score the catalog; the top ranks get answered in copy slots",
        "branches": obj["branches"] if obj else [],
        "outcome": obj["output"] if obj else f"{len(pri)} objections ranked",
        "why": obj["why"] if obj else "",
        "rows": obj_rows or [{"label": "No objections matched", "value": "generic proof and CTAs ship",
                              "fired": False, "policy": None}],
    })

    tier_stage = by_id.get("tier")
    conf = page.get("confidence", {})
    gates = (II.load_image_config("gauntlet").get("guardrails") or {}).get("tier_gates") or {}
    gate_rows = [
        {"label": "Confidence read",
         "value": f"location {conf.get('location', '—')} · company {conf.get('company', '—')} · "
                  f"industry {conf.get('industry', '—')}",
         "fired": True, "policy": "steer"},
        {"label": "Industry look",
         "value": f"only shapes copy and imagery from confidence level {gates.get('industry', 2)} "
                  "(company + industry resolved)", "fired": page.get("tier", 0) >= gates.get("industry", 2),
         "policy": "steer"},
        {"label": "Region mood",
         "value": f"only shapes imagery from confidence level {gates.get('region_mood', 1)} "
                  "(geo confidence)", "fired": page.get("tier", 0) >= gates.get("region_mood", 1),
         "policy": "steer"},
        {"label": "Always",
         "value": "confidence gates what may shape the page — never what it recites",
         "fired": False, "policy": "hold"},
    ]
    cards.append({
        "id": "tiergate", "title": "Confidence gate",
        "subtitle": "How much the anonymous connection is allowed to shape",
        "branches": tier_stage["branches"] if tier_stage else [],
        "outcome": f"confidence {page.get('tier', 0)} · {page.get('tier_label', 'neutral')}",
        "why": tier_stage["why"] if tier_stage else "", "rows": gate_rows,
    })
    return cards


def _copy_cards(page: dict) -> list[dict]:
    """One card per copy slot: shipped vs generic, rule fired, policy, guardrails."""
    cards = []
    for d in page.get("copy_diff", []):
        pol = d.get("policy", "say")
        guards = []
        if d.get("blocked_say"):
            guards.append({"kind": "blocked", "text": f"Blocked say-variant: “{d['blocked_say']}”"})
        if pol == "allude" and d.get("changed"):
            guards.append({"kind": "steer", "text": "Steer-only: inferred data shapes this slot but is never quoted"})
        if pol == "hold":
            guards.append({"kind": "hold", "text": "Hold: the fact behind this slot never ships"})
        guards.append({"kind": "always",
                       "text": "Always on: no company names from IP alone, no behavioral micro-details, "
                               "no bought demographics on the page"})
        cards.append({
            "slot_id": d.get("slot", ""),
            "slot": d.get("label") or d.get("slot", "—"),
            "generic": d.get("generic") or "—",
            "shipped": d.get("shipped") or "—",
            "changed": bool(d.get("changed")),
            "policy": _pol_word(pol),
            "source": (d.get("source") or "—"),
            "why": d.get("why", ""),
            "reason": _marketer_reason(d),
            "blocked_say": d.get("blocked_say"),
            "guards": guards,
        })
    return cards


def _load_policy(cached: bool, prebuild: bool | None, api_key_set: bool) -> tuple[str, str]:
    """Classify a state's image load behaviour → (status, plain-English note)."""
    if cached and prebuild:
        return ("pre-built", "baked into the deploy image — instant on every visit")
    if cached:
        return ("warm", "cached at runtime — instant until the next deploy wipes it")
    if api_key_set:
        return ("live", "first visitor waits ~30s behind a branded gradient; cached after that")
    return ("fallback-only", "no image API key here — gradient/gallery ships, nothing generates")


def _delivery(page: dict) -> dict:
    """Manifest-driven cache/liveness inventory — deterministic disk reads, no API calls."""
    api_key_set = bool(IG._api_key())
    rows = []
    cached_n = prebuilt_n = 0
    for st in PB.manifest_all_states():
        p = GS.build_page(_ConsoleReq(dict(st["params"])), email=st["email"])
        surface_id = st["surface_id"]
        resolved = IG._resolve_prompts(IG.build_image_ctx(p), surface_id=surface_id)
        cached = IG._load_cached(resolved["gen_disk_key"]) is not None
        status, note = _load_policy(cached, st["prebuild"], api_key_set)
        cached_n += 1 if cached else 0
        prebuilt_n += 1 if st["prebuild"] else 0
        surf = IG.surface_spec(surface_id)
        rows.append({
            "id": st["id"], "label": st["label"], "tier": resolved["tier"],
            "surface_id": surface_id, "surface_label": surf["label"],
            "prebuild": st["prebuild"], "cached": cached,
            "status": status, "note": note,
            "disk_key": resolved["gen_disk_key"],
        })
    return {
        "rows": rows, "cached": cached_n, "total": len(rows), "prebuilt": prebuilt_n,
        "api_key_set": api_key_set,
        "ops_rule": "railway run python -m scripts.warm_hero_cache",
        "graph_summary": [
            "Image on disk → serves inline, instantly (pre-built states survive deploys)",
            "Miss + API key → page ships the gradient; the image generates once (~30s) and stays cached",
            "Miss + no key → curated gallery (when an industry resolved) or the CSS gradient — never blocks",
            "Before deploy: the warm script generates every `prebuild: true` state × surface in the manifest",
        ],
    }


def _surface_decision(page: dict, surface_id: str, hi: dict, hid: dict) -> str:
    """Plain-English one-liner: why this image for this visitor."""
    hero = page.get("sections", {}).get("hero", {})
    conv = hid.get("conversion") or {}
    intents = (hid.get("intent_selection") or {}).get("intents") or []
    primary = next((i for i in intents if i.get("primary")), intents[0] if intents else None)
    intent_id = primary["intent_id"].replace("_", " ") if primary else "default gradient"
    drives = conv.get("drives_action") or hero.get("cta_primary", "")
    spec = IG.surface_spec(surface_id)
    if surface_id == "og":
        return (
            f"Decision: social preview uses the same {intent_id} strategy as the hero, "
            f"reframed as a 1200×630 share card — paired with “{drives}” when the link unfurls"
        )
    return (
        f"Decision: hero background uses {intent_id} visual strategy"
        f" — paired with “{drives}” CTA"
    )


def _image_surface_card(page: dict, delivery: dict, surface_id: str) -> dict:
    """One image surface card: intent, prompt, guardrails, tier, load policy."""
    surfaces = page.get("image_surfaces") or {}
    hi = surfaces.get(surface_id) or page.get(f"{surface_id}_image") or page.get("hero_image") or {}
    hid = hi.get("dev") or IG.image_surface_dev_panel(hi, surface_id=surface_id)
    sel = hid.get("intent_selection") or {}
    prompt = hid.get("prompt") or {}
    guard = hid.get("guardrails") or {}
    tier = hid.get("tier") or {}
    receipt = hid.get("receipt") or {}
    spec = IG.surface_spec(surface_id)

    resolved = IG._resolve_prompts(IG.build_image_ctx(page), surface_id=surface_id)
    disk_key = resolved["gen_disk_key"]
    cached = IG._load_cached(disk_key) is not None
    state = next((r for r in delivery["rows"]
                  if r["disk_key"] == disk_key and r["surface_id"] == surface_id), None)
    status, note = _load_policy(cached, state["prebuild"] if state else None,
                                delivery["api_key_set"])

    return {
        "id": surface_id,
        "label": spec["label"],
        "placement": spec.get("placement", ""),
        "surface": spec["label"],
        "url": hi.get("url"),
        "source": receipt.get("source", "gradient"),
        "decision": _surface_decision(page, surface_id, hi, hid),
        "tier_summary": _visual_decision(page)["tier_summary"] if surface_id == "hero" else (
            (tier.get("label") or "Segment base visual")
        ),
        "intent": {
            "rule_fired": sel.get("rule_fired", ""),
            "primary_id": sel.get("primary_id"),
            "intents": [{"id": i["intent_id"], "rank": i["rank"], "why": i.get("why", ""),
                         "signals": i.get("signals") or [], "primary": i.get("primary", False)}
                        for i in sel.get("intents") or []],
        },
        "prompt": {
            "metaphor": prompt.get("visual_metaphor") or "—",
            "composition": prompt.get("composition") or "—",
            "mood": prompt.get("mood") or "—",
            "must_include": prompt.get("must_include") or [],
            "must_avoid": prompt.get("must_avoid") or [],
        },
        "guardrails": {
            "applied": [g["label"] for g in guard.get("applied") or []],
            "blocked": [g["label"] for g in guard.get("blocked") or []],
        },
        "tier": {
            "mode": tier.get("mode", "base_only"), "label": tier.get("label", ""),
            "base_cache_key": tier.get("base_cache_key"),
            "delta_cache_key": tier.get("delta_cache_key"),
            "delta_signals": tier.get("delta_signals") or [],
            "tokens_saved": tier.get("tokens_saved_estimate"),
        },
        "load": {
            "status": status, "note": note, "cached": cached,
            "state_id": state["id"] if state else None,
            "state_label": state["label"] if state else "not a catalogued demo state",
            "prebuild": state["prebuild"] if state else None,
            "surface_id": surface_id,
        },
    }


def _hero_image_card(page: dict, delivery: dict) -> dict:
    """Backward-compatible alias — hero surface card."""
    return _image_surface_card(page, delivery, "hero")


def _guardrail_groups(page: dict) -> dict:
    """Every guardrail from the tenant config + the copy-side policy rules, as controls."""
    config = II.load_image_config("gauntlet")
    yaml_avoid = (config.get("prompt_defaults") or {}).get("must_avoid") or []
    global_avoid = set(II.GLOBAL_MUST_AVOID)
    image_rules = []
    for i, text in enumerate(yaml_avoid):
        image_rules.append({
            "id": f"avoid-{i}", "text": text,
            "locked": text in global_avoid,
            "scope": "all image surfaces (hero, Open Graph, …)",
            "yaml_line": f'  - "{text}"',
        })

    gates = (config.get("guardrails") or {}).get("tier_gates") or {}
    gate_meaning = {
        "industry": "industry-matched environment may only apply from this confidence level",
        "region_mood": "regional mood may only apply from this confidence level",
    }
    tier_gates = [{"key": k, "value": v, "levels": [0, 1, 2, 3],
                   "meaning": gate_meaning.get(k, k),
                   "yaml_line": f"    {k}: {v}"}
                  for k, v in gates.items()]

    intent_blocks = [{"intent": i["id"],
                      "blocked": i.get("blocked_signals") or []}
                     for i in config.get("intents") or []]

    copy_rules = [
        {"text": "say — only facts the visitor typed or logged in with may be quoted",
         "scope": "every copy slot", "locked": True},
        {"text": "steer — inferred/bought data shapes tone, emphasis and order; never quoted",
         "scope": "every copy slot", "locked": True},
        {"text": "hold — modeled income, precise geo, behavioral micro-details never ship",
         "scope": "every copy slot", "locked": True},
        {"text": "no company names from IP alone; no “you bounced at step 3” recitation; "
                 "ad demographics steer internally only",
         "scope": "hero, proof, CTAs", "locked": True},
    ]

    n_fired = sum(1 for d in page.get("copy_diff", []) if d.get("blocked_say"))
    n_fired += len(page.get("objections", {}).get("blocked") or [])
    hid = (page.get("hero_image") or {}).get("dev") or {}
    n_fired += len((hid.get("guardrails") or {}).get("applied") or [])

    return {
        "image_rules": image_rules,
        "tier_gates": tier_gates,
        "intent_blocks": intent_blocks,
        "copy_rules": copy_rules,
        "config_path": "rules/gauntlet_image.yaml",
        "fired_this_visit": n_fired,
    }


class _ConsoleReq:
    """Minimal request stand-in for offline build_page() — same pattern as tests."""
    client = None

    def __init__(self, params: dict | None = None):
        self.query_params = params or {}
        self.headers = {}
        self.cookies = {}


def _overview(page: dict, workflow: list[dict], guardrails: dict) -> dict:
    diff = page.get("copy_diff", [])
    changed = sum(1 for d in diff if d.get("changed"))
    blocked = (sum(1 for d in diff if d.get("blocked_say"))
               + len(page.get("objections", {}).get("blocked") or []))
    hi_src = ((page.get("hero_image") or {}).get("receipt") or {}).get("source", "gradient")
    og_src = ((page.get("og_image") or {}).get("receipt") or {}).get("source", "gradient")
    n_surfaces = len(page.get("image_surfaces") or {"hero": page.get("hero_image")})
    return {
        "numbers": [
            {"n": f"{changed}/{len(diff)}", "label": "copy slots changed"},
            {"n": str(n_surfaces), "label": f"image surfaces ({hi_src} + {og_src})"},
            {"n": str(guardrails["fired_this_visit"]), "label": "guardrails fired"},
            {"n": str(blocked), "label": "blocked variants"},
        ],
        "taken_path": [{"title": s["title"], "outcome": s["outcome"]}
                       for s in workflow if not s["skipped"]],
    }


def _channel_context(page: dict) -> dict:
    """Arrival channel summary for the marketer console header strip."""
    entry = page["entry"]
    ad = page.get("ad_variant")
    ctx = {
        "channel": entry.get("channel", "direct"),
        "channel_label": entry.get("channel_label", "Direct"),
        "utm_campaign": entry.get("utm_campaign") or None,
        "ad_variant": ad["variant_id"] if ad else None,
        "ad_targeting": ad["x_targeting_type"] if ad else None,
    }
    return ctx


def _page_params_for_prompts(page: dict) -> dict:
    """Query params to merge into design_prompts resolve_example for this visit."""
    entry = page["entry"]
    params: dict = {}
    for key in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "ref"):
        val = entry.get(key)
        if val:
            params[key] = val
    det = page.get("det") or {}
    if det.get("ip"):
        params["ip"] = det["ip"]
    ident = page.get("identity") or {}
    if ident.get("kind") == "cohort":
        cohort = ident.get("cohort") or {}
        if cohort.get("email"):
            params["email"] = cohort["email"]
    return params


def _prompt_catalog(page: dict) -> dict:
    """Read-only design_prompts entries matching this visit's channel (+ intent highlight)."""
    channel = page["entry"].get("channel", "direct")
    surfaces = set((page.get("image_surfaces") or {}).keys()) or {"hero"}
    hid = (page.get("hero_image") or {}).get("dev") or {}
    primary_intent = (hid.get("intent_selection") or {}).get("primary_id")
    params = _page_params_for_prompts(page)

    refs: list[dict] = []
    for entry in DP.list_entries(tenant="gauntlet", channel=channel, kind="image"):
        if entry.get("surface") not in surfaces:
            continue
        try:
            resolved = DP.resolve_example(entry["id"], params)
        except (KeyError, ValueError):
            resolved = (entry.get("example_resolved") or "").strip()
        preview = resolved[:480] + ("…" if len(resolved) > 480 else "")
        refs.append({
            "id": entry["id"],
            "surface": entry.get("surface", "hero"),
            "intent": entry.get("intent", ""),
            "channel": entry.get("channel", channel),
            "matches_intent": bool(primary_intent and entry.get("intent") == primary_intent),
            "resolved_preview": preview,
        })
    if primary_intent:
        refs.sort(key=lambda r: (not r["matches_intent"], r["id"]))
    return {
        "channel": channel,
        "channel_label": page["entry"].get("channel_label", channel),
        "primary_intent": primary_intent,
        "entries": refs,
        "config_path": "rules/design_prompts.yaml",
    }


def build_business_console_view(page: dict) -> dict:
    """Everything the marketer console template needs beyond the classic view."""
    pmap = GS.process_map(page)
    workflow = _workflow(page, pmap)
    guardrails = _guardrail_groups(page)
    delivery = _delivery(page)
    return {
        "overview": _overview(page, workflow, guardrails),
        "workflow": workflow,
        "inputs": pmap["inputs"],
        "signals": _signals_in(page),
        "decisions": _decision_cards(page, pmap),
        "copy_cards": _copy_cards(page),
        "image_cards": [_image_surface_card(page, delivery, sid)
                        for sid in _IMAGE_SURFACE_ORDER
                        if (page.get("image_surfaces") or {}).get(sid)
                        or sid == "hero"],
        "guardrails": guardrails,
        "delivery": delivery,
        "channel_context": _channel_context(page),
        "prompt_catalog": _prompt_catalog(page),
        "config_paths": {"image": "rules/gauntlet_image.yaml",
                         "prebuild": "rules/gauntlet_prebuild.yaml",
                         "prompts": "rules/design_prompts.yaml"},
    }


def build_business_dev_view(page: dict) -> dict:
    """Transform build_page() output into the marketer console view model."""
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
        "console": build_business_console_view(page),
    }
