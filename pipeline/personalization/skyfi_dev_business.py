"""Marketing decision log for /skyfi/dev/business — campaign ops view for marketers.

Deterministic transform of the `page` dict from SS.build_page() into decision rows
a marketer can audit: arrival, segment, LOCATION × INDUSTRY / AOI policy (the SkyFi
differentiator, incl. the S09 declared-AOI flip), copy slots, visual, CRM steering.
No LLM, no extra state — same inputs as /skyfi/dev.
"""
from __future__ import annotations

from pipeline.observability import api_costs as AC
from pipeline.personalization import image_gen as IG
from pipeline.personalization import section_obs as OBS
from pipeline.personalization import sections as SEC
from pipeline.personalization import skyfi_site as SS

_AUDIENCE_LABELS = {
    "enterprise": "Enterprise / tasking programs (direct sales)",
    "selfserve": "Self-serve order flow (browse & task)",
    "neutral": "Mixed intent — no strong segment signal yet",
}

_SEGMENT_PERSONAS = {
    "mining": "Mining — site monitoring / mine-planning self-serve track",
    "construction": "Construction — progress-documentation self-serve track",
    "agriculture": "Agriculture — region-scale condition-check self-serve track",
    "energy": "Energy & Infrastructure — asset-monitoring self-serve track",
    "insurance": "Insurance — before/after claims enterprise track",
    "defense": "Defense & Intelligence — AOR/mission enterprise track (strict hold register)",
}

_NETWORK_READ = {
    "corporate": "Corporate IP → enterprise / tasking-program track is likelier",
    "corporate (via VPN)": "Corporate network (possibly VPN) → enterprise framing",
    "residential": "Residential connection → practitioner / self-serve order-flow track",
    "consumer ISP": "Consumer ISP → practitioner / self-serve order-flow track",
    "mobile": "Mobile connection → practitioner / self-serve order-flow track",
}

_FIRMOGRAPHIC_READ = {
    0: "No firmographic hint — copy stays neutral; entry channel leads",
    1: "Geo hint only — the basin/region archive claim may ship, never their exact site",
    2: "Industry signal — tailor sector lines and emphasis (never company name)",
    3: "Strong firmographic signal — sector + region framing, still no creepy recitation",
}

_SLOT_LABELS = {
    "hero_eyebrow": "Hero eyebrow",
    "hero_sub": "Hero headline + sub",
    "hero_cta": "Hero CTAs",
    "hero_location": "Hero location line",
    "how_intro": "How-it-works intro",
    "pricing_body": "Pricing / AOI callout",
    "compare_emphasis": "Comparison table emphasis",
    "final_cta": "Final CTA block",
}

_LOCATION_REGISTER = {
    "region": "Basin/region-scale claim (allude — arm Ex holds exact site)",
    "declared_aoi": "Declared first-party AOI (say — the S09 flip: they told us)",
    "aor": "AOR register (defense guardrail — strict hold)",
    "none": "No claim — location unknown",
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
        low = src.lower()
        if "ad variant" in low:
            parts.append(f"Campaign match ({src})")
        elif any(w in low for w in ("aoi", "aor", "basin", "location", "region", "geo")):
            parts.append(f"Location signal ({src})")
        elif "reverse-ip" in low or "firmographic" in low:
            parts.append("Firmographic hint shapes copy — never recited")
        elif "hubspot" in low or "crm" in low or "archetype" in low:
            parts.append(f"CRM signal ({src})")
        elif "identity" in low or "work-email" in low:
            parts.append(f"First-party identity ({src})")
        elif "audience" in low or "campaign" in low:
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
            {"label": "X vertical", "value": ad.get("segment", "—"),
             "note": _SEGMENT_PERSONAS.get(ad.get("segment", ""), "one of SkyFi's UC2 verticals")},
            {"label": "Ad variant", "value": ad["variant_id"],
             "note": f"utm_campaign={ad['utm_campaign']}"},
            {"label": "Ad hook (clicked)", "value": f"“{ac.get('trigger', '')}”"},
            {"label": "Ad body", "value": ac.get("body", "—")},
            {"label": "Ad CTA", "value": ac.get("cta_label", "—")},
            {"label": "Message-match rule",
             "value": f"Hero must echo ad promise: “{ad['page']['h1_pre']}{ad['page']['h1_blue']}”",
             "note": "Landing headline, eyebrow, how-intro, and CTAs continue the ad conversation"},
        ])
        if ad.get("hold_note"):
            rows.append({"label": "Hold policy", "value": ad["hold_note"],
                         "note": "the vertical's guardrail rides along with the campaign"})
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
                     "value": "Direct visit — IP firmographics, location×industry, and CRM (if any) steer copy",
                     "note": entry.get("why", "")})

    decision = f"Decision: classify as {entry['channel_label'].lower()}"
    if ad:
        decision += f" → message-match {ad.get('segment', 'vertical')} ad variant {ad['variant_id']}"
    elif entry.get("utm_campaign"):
        decision += f" → honor utm_campaign={entry['utm_campaign']}"
    else:
        decision += " → no ad promise to match"

    return {"channel": entry["channel_label"], "decision": decision, "rows": rows}


def _location_read(page: dict) -> dict:
    """The SkyFi differentiator — location × industry + the AOI policy — as a
    marketer-facing decision entry (incl. the S09 declared-AOI flip)."""
    loc = page.get("location") or {}
    mode = loc.get("mode", "none")
    receipt = loc.get("receipt")
    rows: list[dict] = [
        {"label": "Region (geo-IP)", "value": loc.get("region") or page["det"].get("region") or "—"},
        {"label": "Sector lens", "value": loc.get("segment") or "— (no sector resolved)"},
        {"label": "Register", "value": _LOCATION_REGISTER.get(mode, mode)},
    ]
    if loc.get("line"):
        rows.append({"label": "Shipped line", "value": f"“{loc['line']}”"})
    if loc.get("blocked_say"):
        rows.append({"label": "Blocked recite", "value": f"“{loc['blocked_say']}”",
                     "note": "exact-site precision is held (arm Ex) — never demonstrated uninvited"})
    if receipt:
        rows.extend([
            {"label": "AOI on file", "value": receipt.get("aoi_label", "—"),
             "note": f"scale: {receipt.get('aoi_scale', 'site')}"},
            {"label": "Say basis", "value": receipt.get("basis", "declared_first_party"),
             "note": receipt.get("say_reason", "")},
            {"label": "AOI source", "value": receipt.get("source", "—")},
        ])

    if mode == "declared_aoi":
        decision = ("Decision: recite the declared AOI — they drew the boundary themselves in "
                    "the order flow, so exact scale is honest, not surveillance (the S09 flip); "
                    "the 'you told us' receipt ships with it")
    elif mode == "region":
        decision = ("Decision: ship the basin/region archive claim — the archive genuinely "
                    f"covers {loc.get('region')}, so region scale converts without creeping; "
                    "exact-site pinpointing stays held (arm Ex)")
    elif mode == "aor":
        decision = ("Decision: defense audience — AOR/theater register only, never a specific "
                    "asset or their own installation, regardless of tier or login")
    else:
        decision = "Decision: hold all location claims — no location confidence for this visitor"
    return {"mode": mode, "decision": decision, "rows": rows,
            "why": loc.get("why", "")}


def _audience_read(page: dict) -> dict:
    det = page["det"]
    ad = page.get("ad_variant")
    audience = page.get("audience", "neutral")
    tier = page.get("tier", 0)
    net = det.get("network_type") or "unknown"

    if ad:
        segment = _SEGMENT_PERSONAS.get(ad.get("segment", ""), ad.get("segment", "—"))
        segment_note = f"Ad vertical: {ad.get('segment', '—')} → audience {ad.get('audience', '—')}"
    else:
        segment = _AUDIENCE_LABELS.get(audience, audience)
        segment_note = page.get("audience_rule") or ""

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
        signals.append({"label": "Location signal", "value": f"Region: {det['region']} — the "
                        "basin/region archive claim is live for this visitor"})

    ident = page.get("identity")
    if ident:
        if ident.get("kind") == "cohort":
            arch = ident.get("archetype", {})
            signals.append({"label": "CRM segment",
                            "value": f"{arch.get('label', 'Known lead')} — {arch.get('reason', '')}"})
            aoi = ((ident.get("view") or {}).get("declared") or {}).get("aoi")
            if aoi:
                signals.append({"label": "Declared AOI",
                                "value": f"{aoi.get('label', '—')} — first-party, drawn in the "
                                         "order flow; exact scale unlocks (S09)"})
        elif ident.get("kind") == "resolved":
            co = (ident.get("resolved") or {}).get("company")
            signals.append({"label": "Login signal",
                            "value": "Work email" + (f" from {co}" if co else "")})

    route = _AUDIENCE_LABELS.get(audience, audience)
    decision = f"Decision: route to {route}"
    if ad:
        decision += f" — ad names the {ad.get('segment', 'vertical')} vertical"
    elif tier >= 2 and det.get("industry"):
        decision += f" — industry hint ({det['industry']}) steers sector lines and emphasis"
    elif net in ("corporate", "corporate (via VPN)"):
        decision += " — corporate network leans enterprise / tasking-program track"

    return {
        "segment": segment,
        "segment_note": segment_note,
        "decision": decision,
        "signals": signals,
    }


def _copy_decisions(page: dict) -> list[dict]:
    out: list[dict] = []
    for d in page.get("copy_diff", []):
        out.append({
            "slot": d.get("label") or _SLOT_LABELS.get(d.get("slot", ""), d.get("slot", "—")),
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
    brain = hid.get("brain") or page.get("brain_sim") or {}
    conv = hid.get("conversion") or {}
    prompt = hid.get("prompt") or {}
    tier = hid.get("tier") or {}
    intents = (hid.get("intent_selection") or {}).get("intents") or []
    primary = next((i for i in intents if i.get("primary")), intents[0] if intents else None)

    intent_id = primary["intent_id"].replace("_", " ") if primary else "default gradient"
    intent_why = primary.get("why", "reinforces the hero CTA emotionally") if primary else "—"
    mood = prompt.get("mood") or "Operational, orbital, confident"
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
                friendly.append(s.split(":", 1)[1] + " region — the location signal reaches the image")
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
    if brain.get("brain_score") is not None:
        decision += (f" · brain_score {brain['brain_score']:.2f}"
                     f" ({brain.get('brain_simulator') or 'proxy_v1'})")
    elif brain.get("brain_target"):
        decision += f" · brain_target {brain['brain_target']}"

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
        "hero_motion_url": hi.get("motion_url"),
        "hero_motion_metaphor": (hid.get("motion") or {}).get("motion_metaphor"),
        "hero_motion_framing": (hid.get("motion") or {}).get("framing"),
        "tier_summary": tier_summary,
        "tier_mode": tier_mode,
        "brain_target": brain.get("brain_target"),
        "brain_target_label": brain.get("brain_target_label"),
        "brain_score": brain.get("brain_score"),
        "brain_simulator": brain.get("brain_simulator"),
        "candidates_evaluated": brain.get("candidates_evaluated"),
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
                f"Declared goal “{v['declared']['goal']}” → copy can say it (first-party)"
            )
        aoi = v.get("declared", {}).get("aoi")
        if aoi:
            steering.append(
                f"Declared AOI “{aoi.get('label', '—')}” → the exact-scale location line may "
                "recite it — they drew the boundary themselves (S09)"
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
            "declared_aoi": (aoi or {}).get("label"),
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

    ad = page.get("ad_variant")
    if ad and ad.get("hold_note"):
        held.append(ad["hold_note"])

    loc = page.get("location") or {}
    if loc.get("mode") == "declared_aoi":
        said.append("Declared AOI — recited at exact scale because they drew it themselves (S09)")
    elif loc.get("line"):
        steered.append("Location line: basin/region archive claim — never exact-site scale")
    if loc.get("blocked_say"):
        held.append("Exact-site precision (arm Ex) — never demonstrated uninvited")

    ident = page.get("identity")
    if ident and ident.get("kind") == "cohort":
        said.append("First name & declared form answers — stated when logged in")
        steered.append("Employer/title from enrichment — steers tone, never quoted on page")
        held.append("Modeled income & precise geo — never displayed")
    elif ident and ident.get("kind") == "resolved":
        said.append("Company name from work email domain — fair game to say aloud")

    return {
        "said": said or ["Only first-party declared facts when the visitor identifies themselves"],
        "steered": steered or ["Anonymous firmographics, region, and ad context shape copy without naming the visitor"],
        "held": held or ["No blocked facts for this visitor"],
        "rules": [
            "We steer on region and sector — we never name their company from IP alone",
            "Location claims stay at basin/region scale — exact-AOI ships only when declared first-party (the S09 flip)",
            "Defense audiences get the AOR register — their own installations are never referenced",
            "Ad targeting demographics steer internally — never appear on page",
        ],
    }


# --------------------------------------------------------------------------- #
# Section designer (S5/T-07b) — one card per registry section, read-only values
# from rules/skyfi_sections.yaml + this visit's page dict. Edits stage YAML
# diffs to the registry via the shared drawer; nothing writes server-side.
# DOM contract: 04-spec/contracts/designer-dom.md (sd-* testids).
# --------------------------------------------------------------------------- #
_SD_TENANT = "skyfi"
_SD_ROUTES = list(SS.ORDER_BY_AUDIENCE)          # enterprise · selfserve · neutral
_SD_STRATEGIES = ["objection-reframe", "social-proof", "authority", "scarcity-honest",
                  "loss-aversion", "location-relevance", "message-match", "neutral"]
_SD_LAWFUL = {
    "say": "first-party / declared — may be quoted",
    "allude": "inferred or bought — steers only, never quoted",
    "hold": "held — never reaches the page",
}


def _sd_latency(kind: str, mode: str | None, workflow: str) -> dict:
    """Q8 latency class per designer-dom.md: instant | ~2s swap | blocking⚠."""
    if kind == "text":
        if mode == "deterministic" or workflow == "prebuilt":
            return {"cls": "instant", "label": "instant"}
        return {"cls": "swap", "label": "~2s swap"}
    if workflow == "prebuilt":
        return {"cls": "instant", "label": "instant"}
    if workflow == "realtime":
        return {"cls": "swap", "label": "~2s swap"}
    return {"cls": "blocking", "label": "blocking⚠"}


def _sd_text_cost(mode: str, workflow: str) -> str:
    if mode == "deterministic":
        return "$0 / visit — deterministic slot-fill"
    if workflow == "prebuilt":
        return "$0 / visit — Gate-cleared pool replays from cache"
    return "LLM cost on first visit · cached by visit key after"


def _sd_gate_verdict(d: dict | None, policy_live: str) -> dict:
    if d is None:
        return {"status": "pass", "reason": "registry target — no live slot bound this visit"}
    if d.get("blocked_say"):
        return {"status": "pass", "reason": "shipped copy cleared — 1 say-variant held by policy"}
    return {"status": "pass", "reason": f"cleared under the {policy_live} policy"}


def _sd_text_target(t: dict, d: dict | None, rules_version: str) -> dict:
    policy_live = (d or {}).get("policy") or t.get("policy", "allude")
    verdict = _sd_gate_verdict(d, policy_live)
    mode, workflow = t.get("mode", "deterministic"), t.get("workflow", "realtime")
    cache_key = ("— deterministic slot-fill, no cache needed" if mode == "deterministic"
                 else f"pool:{t['slot_id']}")
    return {
        "slot_id": t["slot_id"],
        "label": t.get("label") or t["slot_id"],
        "mode": mode, "workflow": workflow,
        "strategy": t.get("strategy", "neutral"),
        "policy": t.get("policy", "allude"),
        "policy_live": policy_live,
        "prompt": t.get("prompt") or "",
        "gate_rule": t.get("gate") or f"{_SD_TENANT}_tenant",
        "source": t.get("source", "catalog"),
        "claims": t.get("claims") or [],
        "shipped": ((d or {}).get("shipped") or "—")[:220],
        "generic": ((d or {}).get("generic") or "—")[:220],
        "changed": bool((d or {}).get("changed")),
        "gate": verdict,
        "latency": _sd_latency("text", mode, workflow),
        "cost": _sd_text_cost(mode, workflow),
        "receipt": {
            "source_id": (d or {}).get("source") or t.get("source", "catalog"),
            "lawful_basis": _SD_LAWFUL.get(policy_live, policy_live),
            "policy": policy_live,
            "gate_verdict": verdict["status"],
            "claim_ids": ", ".join(t.get("claims") or []) or "—",
            "cache_key": cache_key,
            "mode": mode, "workflow": workflow,
            "rules_version": rules_version,
        },
        "held_say": bool((d or {}).get("blocked_say")),
        "ab": {"routes": _SD_ROUTES,
               "note": "posteriors per route arrive with the per-decision pool — "
                       "a random-control holdout measures lift"},
        "drift": {"status": "active", "rules_version": rules_version},
    }


def _designer_view(page: dict) -> dict:
    """Everything the per-section designer cards need (read-only this wave).

    T-04 parity: the graph/evals/observe/ab/drift panels + the cost row are built by
    pipeline/personalization/section_obs.py from this request's real build, the live
    api-cost ledger, and the seeded per-decision pool campaign (labeled seeded).
    SkyFi note (S02): the registry seeds every image workflow as realtime — the
    latency badges show the ~2s gradient→swap class, never blocking."""
    secs = SEC.list_sections(_SD_TENANT)
    rules_version = SEC.registry_version(_SD_TENANT)
    diff_by_slot = {d.get("slot"): d for d in page.get("copy_diff", [])}
    per_gen = AC.estimate_cost(service="gemini_image", model=IG.DEFAULT_MODEL,
                               images_generated=1)
    hi = page.get("hero_image") or {}
    hid = hi.get("dev") or (IG.hero_image_dev_panel(hi) if hi else {})
    brain = (hid.get("brain") or page.get("brain_sim") or {})
    entry = page["entry"]
    route = page.get("audience", "neutral")
    tier, tier_label = page.get("tier", 0), page.get("tier_label", "neutral")
    entry_signals = " · ".join(f"{s['label']}={s['value']}" for s in entry["signals"]
                               if s["value"] != "—")
    gate_rules_version = OBS.seeded_campaign(_SD_TENANT,
                                             tuple(_SD_ROUTES))["gate_rules_version"]

    seq = 0
    out_sections: list[dict] = []
    for sec in secs:
        text_targets: list[dict] = []
        diff_rows: list[dict] = []
        for t in sec.get("text_targets") or []:
            d = diff_by_slot.get(t["slot_id"])
            if d:
                diff_rows.append(d)
            tt = _sd_text_target(t, d, rules_version)
            tt["ab"] = OBS.ab_panel(_SD_TENANT, sec["id"], t["slot_id"], _SD_ROUTES,
                                    kind="text")
            tt["drift"] = OBS.drift_status(_SD_TENANT, sec["id"], t["slot_id"],
                                           rules_version, _SD_ROUTES, kind="text")
            text_targets.append(tt)

        image_targets: list[dict] = []
        for t in sec.get("image_targets") or []:
            surf = t["surface_id"]
            workflow = t.get("workflow", "realtime")
            is_hero = surf == "hero" and bool(hi)
            receipt = (hid.get("receipt") or {}) if is_hero else {}
            tier_i = (hid.get("tier") or {}) if is_hero else {}
            guard = (hid.get("guardrails") or {}) if is_hero else {}
            applied, blocked_g = guard.get("applied") or [], guard.get("blocked") or []
            if workflow == "prebuilt":
                cost = f"${per_gen:.3f}/gen offline · baked before deploy · $0/visit"
            elif workflow == "realtime":
                cost = f"${per_gen:.3f}/gen first visit · $0 after cache-by-key"
            else:
                cost = f"${per_gen:.3f}/gen every uncached visit — discouraged"
            verdict = {"status": "pass",
                       "reason": (f"{len(applied)} guardrails applied"
                                  + (f" · {len(blocked_g)} blocked" if blocked_g else ""))
                       if is_hero else "registry target — not rendered on this page yet"}
            source = receipt.get("source", "gradient") if is_hero else "—"
            sel = (hid.get("intent_selection") or {}) if is_hero else {}
            image_targets.append({
                "surface_id": surf,
                "label": t.get("label") or surf,
                "workflow": workflow,
                "prebuilt_states_cap": t.get("prebuilt_states_cap"),
                "url": hi.get("url") if is_hero else None,
                "source": source,
                "load_status": source if is_hero else "not rendered yet",
                "load_note": ("resolved for this visit — cached by key after first paint"
                              if is_hero else "declared in the registry; the page does not "
                              "render this surface yet"),
                "intent": sel.get("primary_id"),
                "gate": verdict,
                "latency": _sd_latency("image", None, workflow),
                "cost": cost,
                "receipt": {
                    "source_id": source,
                    "lawful_basis": _SD_LAWFUL["allude"],
                    "policy": "allude",
                    "gate_verdict": verdict["status"],
                    "claim_ids": "—",
                    "cache_key": tier_i.get("base_cache_key") or "—",
                    "mode": "generative", "workflow": workflow,
                    "rules_version": rules_version,
                },
                "ab": OBS.ab_panel(_SD_TENANT, sec["id"], surf, _SD_ROUTES, kind="image"),
                "drift": OBS.drift_status(_SD_TENANT, sec["id"], surf, rules_version,
                                          _SD_ROUTES, kind="image"),
            })

        held_count = sum(1 for d in diff_rows if d.get("blocked_say"))
        changed_count = sum(1 for tt in text_targets if tt["changed"])
        sec_cost = OBS.cost_row(sec["id"], [it["receipt"]["cache_key"]
                                            for it in image_targets])
        observe, seq = OBS.ledger_rows(
            seq, section_id=sec["id"], entry_channel=entry.get("channel", "direct"),
            route=route, tier_label=str(tier_label), text_targets=text_targets,
            image_targets=image_targets, cost=sec_cost,
            registry_version=rules_version)

        out_sections.append({
            "id": sec["id"],
            "label": sec.get("label") or sec["id"],
            "region": sec.get("region", sec["id"]),
            "personalize": bool(sec.get("personalize")),
            "goal": sec.get("goal", ""),
            "channels": sec.get("channels") or [],
            "text_targets": text_targets,
            "image_targets": image_targets,
            "graph": OBS.flow_nodes(
                entry_channel=entry.get("channel", "direct"),
                entry_signals=entry_signals, route=route, tier=tier,
                tier_label=str(tier_label), text_targets=text_targets,
                image_targets=image_targets, held_count=held_count,
                changed_count=changed_count, cost=sec_cost,
                rules_version=gate_rules_version, registry_version=rules_version),
            "evals": OBS.eval_rows(sec, text_targets, diff_rows, brain, image_targets),
            "observe": observe,
            "cost": sec_cost,
        })

    channel = page["entry"].get("channel", "direct")
    return {
        "tenant": _SD_TENANT,
        "sections": out_sections,
        "rules_version": rules_version,
        # registry channel vocabulary is "ads"; entry classify says "ad"
        "active_channel": {"ad": "ads"}.get(channel, channel),
        "strategies": _SD_STRATEGIES,
        "config": {
            "sections": f"rules/{_SD_TENANT}_sections.yaml",
            "image": "rules/skyfi_image.yaml",
            "prebuild": "rules/skyfi_prebuild.yaml",
            "copy_module": "pipeline/personalization/skyfi_site.py",
        },
    }


def build_business_dev_view(page: dict) -> dict:
    """Transform build_page() output into marketer decision-log sections."""
    return {
        "arrival": _arrival_attribution(page),
        "audience_read": _audience_read(page),
        "location": _location_read(page),
        "copy_decisions": _copy_decisions(page),
        "visual": _visual_decision(page),
        "lead": _lead_context(page),
        "steering": _steering_vs_saying(page),
        "changed_count": len(_changed_slots(page)),
        "total_slots": len(page.get("copy_diff", [])),
        "designer": _designer_view(page),
    }
