"""Creative agents for /demo/live — copy + design, provable-first, AI on top.

Three pieces, all sourced:
  • ANGLES — deterministic creative briefs (peer-proof / ROI / local / scale / speed). Pick an
    angle, the copy changes. Provable by construction, $0, instant. The always-on fallback.
  • design_select() — the DESIGN AGENT: from the firmographic it picks the image + accent + tone
    and shows *why* (provenance for design, not just copy).
  • ai_copy() + verify_copy() — the GATED COPY AGENT: an LLM proposes copy from a brief, and every
    line runs through a Gate that blocks the unprovable (superlatives, fabricated stats, reciting
    the company under an allude policy). Inert without ANTHROPIC_API_KEY → falls back to the angle.

The thesis: the agent proposes, the Gate disposes. Nothing ships that can't be proven.
"""
from __future__ import annotations

import re

from pipeline.common import config
from pipeline.common.cache import LLMCache
from pipeline.personalization import scene as SC

# --- deterministic creative angles (the briefs) -------------------------------------------
ANGLES = [
    {"key": "default", "label": "Industry default", "brief": "The base industry framing."},
    {"key": "peer", "label": "Peer proof", "brief": "Lead with industry peers / social proof.",
     "eyebrow": "Trusted across {industry}", "headline": "The platform {industry} teams standardize on.",
     "sub": "Operators across {region} run their pipeline on it."},
    {"key": "roi", "label": "ROI / efficiency", "brief": "Lead with measurable efficiency.",
     "eyebrow": "Built for {industry} margins", "headline": "Do more with the team you already have.",
     "sub": "Cut the busywork out of {industry} ops across {region}."},
    # loss-frame: the cost of inaction, not the upside. Loss is felt ~2x an equal gain (prospect
    # theory), and it's provable by construction here — it frames the status quo, never invents a
    # number. The gain-framed sibling of "roi"; the copy research's cost-of-inaction lever.
    {"key": "loss", "label": "Cost of inaction", "brief": "Lead with the cost of the status quo (loss-framed).",
     "eyebrow": "The cost of guessing in {industry}", "headline": "Every line you can’t prove is a risk you can’t see.",
     "sub": "Stop shipping {industry} outreach you can’t stand behind across {region}."},
    {"key": "local", "label": "Local pride", "brief": "Lead with the region.",
     "eyebrow": "For operators across {region}", "headline": "Built for the way {region} works.",
     "sub": "Local-first software for {industry} teams."},
    {"key": "scale", "label": "Scale", "brief": "Lead with scale / growth.",
     "eyebrow": "Engineered for scale", "headline": "Built for {industry} at the pace of growth.",
     "sub": "From first deal to enterprise — across {region}."},
    {"key": "speed", "label": "Speed", "brief": "Lead with time-to-value.",
     "eyebrow": "Live in days, not quarters", "headline": "Get your {industry} team moving this week.",
     "sub": "No rip-and-replace — built for {region} operators."},
]
ANGLE_BY = {a["key"]: a for a in ANGLES}


def angle_copy(industry: str, angle: str, region: str | None, company: str | None = None,
               city: str | None = None, policy: str = "allude") -> dict:
    """Deterministic copy for a (industry × angle). Provable — just templates filled."""
    ind = SC.BY_KEY.get(industry, SC.BY_KEY[SC.DEFAULT_INDUSTRY])
    a = ANGLE_BY.get(angle)
    if not a or a["key"] == "default" or "headline" not in a:
        if policy == "say":
            return SC.build_scene(region, industry, company=company, city=city, policy="say")
        return {"eyebrow": SC._fill(ind["eyebrow"], region), "headline": SC._fill(ind["headline"], region),
                "sub": SC._fill(ind["sub"], region), "cta": ind["cta"]}

    def f(s):
        return s.replace("{industry}", ind["label"].lower()).replace("{region}", region or SC.GENERIC_REGION)
    return {"eyebrow": f(a["eyebrow"]), "headline": f(a["headline"]), "sub": f(a["sub"]), "cta": ind["cta"]}


# --- design agent -------------------------------------------------------------------------
def design_select(*, industry: str, region: str | None = None, company: str | None = None,
                  daypart: str | None = None, idx: int = 0) -> dict:
    """The design agent: pick image + accent + tone from the firmographic, and explain why."""
    ind = SC.BY_KEY.get(industry, SC.BY_KEY[SC.DEFAULT_INDUSTRY])
    img = SC.image_for(industry, idx)
    tone = "calm, low-light" if daypart in ("evening", "late night") else "bright, high-energy"
    rationale = []
    if company:
        rationale.append({"factor": "company resolved from IP", "choice": "firmographic-tailored — but allude (never recited)"})
    rationale += [
        {"factor": f"industry = {ind['label']}", "choice": f"backdrop “{img['id']}” + {ind['accent']} accent"},
        {"factor": f"region = {region or '—'}", "choice": "region-first framing in the copy"},
        {"factor": f"daypart = {daypart or '—'}", "choice": f"{tone} tone"},
    ]
    return {"image": img, "accent": ind["accent"], "tone": tone, "rationale": rationale}


# --- the Gate (focused, for ad-hoc generated copy) ----------------------------------------
_SUPERLATIVES = ("#1", "number one", "the best", "best-in-class", "best in class", "leading",
                 "world's", "world’s", "unrivaled", "unmatched", "guaranteed", "#1 ", "no. 1")
# comparative / competitive claims — the highest-scrutiny class: a superiority claim the Gate
# can't back from a proof store, or reciting a competitor we only *inferred* from the visitor.
_COMPARATIVE = ("better than", "beats ", "outperform", "smarter than", "faster than",
                "cheaper than", " vs ", " vs.", "versus", "unlike ", "switch from", "switch off",
                "replace your", "rip out", "ditch ", "leave behind", "superior to", "win against")
# AI-generated "tells" — the bulk-automation fingerprint. Cold copy sells exactly one thing: that
# a human did the homework; these phrases/words erode it, so the Gate treats them as unshippable.
# Axis B of the Gate (persuasion hygiene) — the per-line, surface-agnostic half of the copy
# research. Message-level limits (one CTA, ≤125 words, no cold calendar link) live in the outbound
# sequence validator, not here, because this Gate verifies single landing-hero lines.
_AI_TELL_PHRASES = ("hope this email finds you well", "hope this finds you well",
                    "hope you're doing well", "hope you are doing well", "i wanted to reach out",
                    "i came across your profile", "i noticed you", "circle back", "touch base",
                    "in today's fast-paced", "at the end of the day")
_AI_TELL_WORDS = ("delve", "leverage", "robust", "pivotal", "seamless", "elevate", "unlock",
                  "synergy", "tapestry", "testament", "moreover", "furthermore", "boasts",
                  "underscore", "game-changer", "ever-evolving")
_AI_TELL_RE = re.compile(r"\b(" + "|".join(_AI_TELL_WORDS) + r")\b")
_EMDASH = "—"


def verify_copy(lines, facts: str, company: str | None, policy: str,
                competitors: list[str] | None = None) -> list[dict]:
    """The Gate for generated copy: block the unprovable AND the unshippable. Every line gets a
    verdict + reason, on two axes:
      A — provability: superlatives, comparatives, an inferred competitor, a number not in the
          sources, or reciting the company under `allude` (highest-scrutiny: comparatives /
          named competitors — blocked by construction, not merely discouraged).
      B — persuasion hygiene: AI-generated tells and em-dash overuse — the bulk-automation
          fingerprint that erodes the one thing cold copy sells. A line that can't be proven OR
          can't be defended as non-spam is structurally unable to ship."""
    out = []
    fl = (facts or "").lower()
    comps = [c.lower() for c in (competitors or []) if c]
    for ln in lines:
        s = (ln or "").lower()
        reason = None
        if any(w in s for w in _SUPERLATIVES):
            reason = "unprovable superlative — no source backs it"
        elif any(w in s for w in _COMPARATIVE):
            reason = "comparative claim — the Gate blocks superiority it can't prove from a source"
        elif any(c in s for c in comps):
            reason = "recites a competitor inferred from the visitor — allude forbids naming it"
        elif re.search(r"\d+\s*%|\b\d+x\b|\$\s?\d", s) and not re.search(r"\d", fl):
            reason = "cites a number that isn't in the sources"
        elif company and policy == "allude" and company.lower() in s:
            reason = "recites the company name — the allude policy forbids it"
        elif any(p in s for p in _AI_TELL_PHRASES):
            reason = "AI-tell phrase — reads as bulk automation, not a human who did the homework"
        elif _AI_TELL_RE.search(s):
            reason = "AI-tell word — the bulk-automation fingerprint; rewrite in plain language"
        elif s.count(_EMDASH) > 1:
            reason = "more than one em-dash — an AI-generated tell; split into short sentences"
        out.append({"line": ln, "ok": reason is None,
                    "reason": reason or "every claim traces to a source — clears the Gate"})
    return out


# --- the message Gate (Axis B at the whole-message scale) — outbound hygiene ----------------
# verify_copy() gates one line; verify_message() gates a whole outbound message: exactly one ask,
# short, no cold calendar link, no spam-promise wording, every line clean of AI-tells/superlatives.
# Vetoes keep a variant OUT of the action pool (the same truth-boundary the claim Gate enforces,
# one level up); warnings are advisory. Wired into build_action_pool() and shown on /policies.
_MSG_MAX_WORDS = {"cold": 125, "warm": 200}
_CTA_MARKER = "→"                                          # the house CTA-button convention
_SPAM_PROMISE = ("free", "guaranteed", "risk-free", "act now", "buy now", "click here",
                 "limited time", "limited spots", "urgent", "no cost")
_SPAM_RE = re.compile(r"\b(" + "|".join(p.replace("-", r"[-\s]").replace(" ", r"\s+")
                                        for p in _SPAM_PROMISE) + r")\b", re.I)
_CALENDAR_LINK = re.compile(r"calendly\.com|cal\.com|savvycal|hubspot\.com/meetings|meetings?\.\w|/book(ing)?\b", re.I)
_MEETING_ASK = ("book a demo", "book a call", "schedule a", "15-minute", "15 minutes",
                "20-minute", "20 minutes", "30-minute", "hop on a call", "set up a meeting", "find a time")
_LINK_RE = re.compile(r"https?://\S+|www\.\S+", re.I)


def _line_is_unclean(line: str) -> str | None:
    """The surface-independent half of the Gate (superlative / comparative / AI-tell / em-dash) —
    shared by every line of a message. Numbers are NOT checked here: in outbound copy they're
    claim-backed and gated by the NLI claim Gate, not this hygiene pass."""
    s = (line or "").lower()
    if any(w in s for w in _SUPERLATIVES):
        return "unprovable superlative"
    if any(w in s for w in _COMPARATIVE):
        return "comparative/superiority claim with no proof"
    if any(p in s for p in _AI_TELL_PHRASES) or _AI_TELL_RE.search(s):
        return "AI-tell phrasing — reads as bulk automation"
    if s.count(_EMDASH) > 1:
        return "more than one em-dash — an AI-generated tell"
    return None


def verify_message(body: str, *, channel: str = "email", stage: str = "cold") -> dict:
    """The Gate at the message scale. Returns vetoes (block: keep it out of the action pool) +
    warnings (advisory), plus the measured word/CTA counts. A message that can't be proven OR
    can't be defended as non-spam is structurally unable to ship — same rule as verify_copy()."""
    body = body or ""
    s = body.lower()
    naked = re.sub(r"\[\[[^\]]+\]\]|\{[^}]+\}", " ", body)      # drop claim markers + slot tokens
    words = len(naked.split())
    cta_count = body.count(_CTA_MARKER)
    links = _LINK_RE.findall(body)
    cap = _MSG_MAX_WORDS.get(stage, _MSG_MAX_WORDS["cold"])
    vetoes: list[str] = []
    warnings: list[str] = []

    if cta_count > 1:
        vetoes.append(f"{cta_count} CTAs — a message gets exactly one ask (choice overload kills reply)")
    if words > cap:
        vetoes.append(f"{words} words > {cap} — over length for a {stage} touch; cut to the one idea")
    if stage == "cold" and _CALENDAR_LINK.search(s):
        vetoes.append("a calendar link in a cold first touch — earn the meeting before you ask for time")
    if len(links) > 1:
        vetoes.append(f"{len(links)} links — one max; extra links read as bulk and hurt deliverability")
    m = _SPAM_RE.search(body)
    if m:
        vetoes.append(f"spam-promise wording (“{m.group(0).strip()}”) — trips filters, reads as a blast")
    for ln in (l for l in body.splitlines() if l.strip()):
        why = _line_is_unclean(ln)
        if why:
            vetoes.append(f"line fails the Gate ({why})")

    if stage == "cold" and any(k in s for k in _MEETING_ASK):
        warnings.append("cold touch leads with a meeting ask — a soft interest question lifts reply")
    if cta_count == 0:
        warnings.append("no CTA — the message never asks for the next step")

    return {"ok": not vetoes, "vetoes": vetoes, "warnings": warnings,
            "words": words, "cta_count": cta_count, "stage": stage}


def verify_sequence(steps: list[str]) -> dict:
    """Sequence-level hygiene the per-message Gate can't see: never single-touch, cap the burnout,
    each step a NEW angle (no “just bumping this” duplicate). Per-message vetoes still apply to
    each step via verify_message()."""
    steps = steps or []
    n = len(steps)
    vetoes: list[str] = []
    warnings: list[str] = []
    if n < 2:
        vetoes.append("single-touch sequence — most replies come from follow-ups; add 3–5 steps")
    if n > 7:
        warnings.append(f"{n} touches — past ~7 the reply rate inverts; trim the tail")
    norm = [re.sub(r"\s+", " ", (st or "").strip().lower()) for st in steps]
    if len(set(norm)) < len(norm):
        vetoes.append("a follow-up repeats a previous step verbatim — each touch needs a new angle")
    return {"ok": not vetoes, "vetoes": vetoes, "warnings": warnings, "touches": n}


def _llm_hero(prompt: str) -> dict | None:
    """One Claude Haiku call → {headline, sub}, cached by prompt (LLMCache). None on any failure /
    no key — caller falls back. The cache cuts a repeat (industry × region × angle × policy) from a
    ~1.3s model call to ~0; only successful drafts are cached, so a transient failure retries."""
    if not config.ANTHROPIC_API_KEY:
        return None
    ck = LLMCache.hash_input("copy_hero_v1", prompt)

    def compute() -> dict:
        import json as _json

        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        r = client.messages.create(model="claude-haiku-4-5-20251001", max_tokens=220,
                                   messages=[{"role": "user", "content": prompt}])
        txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        m = re.search(r"\{.*\}", txt, re.S)
        d = _json.loads(m.group(0)) if m else {}
        if d.get("headline") and d.get("sub"):
            return {"headline": d["headline"].strip(), "sub": d["sub"].strip()}
        raise ValueError("empty draft")   # raise → not cached → a bad call retries next time

    try:
        return LLMCache().get_or_compute(ck, compute) or None
    except Exception:
        return None


def _llm_draft(ind: dict, region: str | None, angle: str) -> dict | None:
    """Ask the LLM for a hero for this (industry × region × angle)."""
    a = ANGLE_BY.get(angle, ANGLE_BY["default"])
    return _llm_hero(
        f"Write a B2B SaaS landing hero for a {ind['label']} company in {region or 'the US'}.\n"
        f"Angle: {a.get('brief', 'clear value')}.\n"
        "Rules: no superlatives (#1/best/leading), no invented stats or numbers, never name the\n"
        "visitor's company. Return JSON only: {\"headline\": \"…\", \"sub\": \"…\"} — headline ≤ 9 words.")


# Tier-3 competitor-research agent ---------------------------------------------------------
# Provable, category-level differentiators — structural properties of a tool that can prove every
# claim. Claims about OUR product (never "we beat X"), so they clear the Gate by construction.
_DIFFERENTIATORS = [
    "every claim ships with its source, basis, and surface policy",
    "it withholds any line it can't prove — by construction",
    "every personalization carries a receipt you can audit",
    "the optimizer only ships variants that already cleared verification",
]
# competitor names used ONLY to BLOCK reciting an inferred competitor (the safe direction).
# Distinctive tokens only — deliberately excludes generic words that double as product
# vocabulary (e.g. "outreach"), which would false-positive on our own copy.
COMPETITOR_HINTS = ("clay", "apollo.io", "salesloft", "zoominfo", "hubspot", "clearbit",
                    "6sense", "rb2b", "common room", "gauntletai")


def _llm_brief(category: str, region: str | None) -> list[str] | None:
    if not config.ANTHROPIC_API_KEY:
        return None
    prompt = (f"You are positioning a provenance-verified GTM/CRM product within the {category} field.\n"
              "List 3 differentiators that are STRUCTURAL properties of a tool that can prove every claim.\n"
              "Rules: do NOT name any competitor. Do NOT claim superiority (no 'better/faster/cheaper than').\n"
              "Each is a provable property of our product, ≤ 12 words. Return JSON: {\"diffs\": [\"…\",\"…\",\"…\"]}.")
    ck = LLMCache.hash_input("copy_brief_v1", prompt)

    def compute() -> dict:
        import json as _json

        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        r = client.messages.create(model="claude-haiku-4-5-20251001", max_tokens=240,
                                   messages=[{"role": "user", "content": prompt}])
        txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        m = re.search(r"\{.*\}", txt, re.S)
        d = _json.loads(m.group(0)) if m else {}
        diffs = [x.strip() for x in (d.get("diffs") or []) if x and x.strip()]
        if diffs:
            return {"diffs": diffs[:3]}
        raise ValueError("no diffs")

    try:
        return (LLMCache().get_or_compute(ck, compute) or {}).get("diffs") or None
    except Exception:
        return None


def competitor_brief(*, industry: str, region: str | None = None, company: str | None = None) -> dict:
    """Tier-3 research agent: a brief of *provable* category differentiators. LLM-assisted when
    keyed, deterministic always. It never names a competitor or asserts superiority — it's
    positioning material; the Gate is what keeps the copy honest downstream."""
    ind = SC.BY_KEY.get(industry, SC.BY_KEY[SC.DEFAULT_INDUSTRY])
    category = f"{ind['label']} GTM / revenue tooling"
    diffs, source = list(_DIFFERENTIATORS), "template"
    llm = _llm_brief(category, region)
    if llm:
        diffs, source = llm, "ai"
    return {"category": category, "differentiators": diffs, "source": source,
            "note": ("Researched by the competitor agent — provable category differentiators only."
                     if source == "ai" else
                     "Competitor agent off (no key) — deterministic differentiators. Same discipline.")}


def ai_copy(*, industry: str, region: str | None, company: str | None, city: str | None,
            angle: str, policy: str, competitive: bool = False) -> dict:
    """The gated copy agent: LLM proposes (if keyed) → Gate verifies → angle falls back.
    Always returns a Gate-blocked example too, so the Gate is visible even with the AI off.
    competitive=True engages the Tier-3 path: positioning that leads with a provable differentiator
    — never naming a competitor or claiming superiority (the Gate enforces both)."""
    ind = SC.BY_KEY.get(industry, SC.BY_KEY[SC.DEFAULT_INDUSTRY])
    facts = f"region={region or '—'}; industry={ind['label']}; company={company or '—'}"

    if competitive:
        brief = competitor_brief(industry=industry, region=region, company=company)
        diff = brief["differentiators"][0] if brief["differentiators"] else "every claim carries a receipt"
        draft = _llm_hero(
            f"Write a B2B SaaS landing hero for a {ind['label']} buyer in {region or 'the US'}.\n"
            f"Lead with this provable differentiator: \"{diff}\".\n"
            "Rules: do NOT name any competitor. Do NOT claim superiority (no 'better/faster/cheaper than',\n"
            "no 'switch from', no 'vs'). No superlatives, no invented numbers.\n"
            "Return JSON only: {\"headline\": \"…\", \"sub\": \"…\"} — headline ≤ 9 words.")
        source = "ai" if draft else "template"
        if not draft:
            draft = {"headline": f"Outreach your {ind['label'].lower()} buyers can trust.",
                     "sub": f"Where others guess, {diff}."}
        checks = verify_copy([draft["headline"], draft["sub"]], facts, company, policy, competitors=COMPETITOR_HINTS)
        # the creepy arm: a named-competitor superiority claim — provably blocked
        blocked = verify_copy(["Switch from Clay — we're faster and cheaper than the rest."],
                              facts, company, policy, competitors=COMPETITOR_HINTS)[0]
        return {"source": source, "headline": draft["headline"], "sub": draft["sub"], "cta": ind["cta"],
                "checks": checks, "blocked_example": blocked, "ships": all(c["ok"] for c in checks),
                "note": brief["note"], "competitive": True, "brief": brief}

    draft = _llm_draft(ind, region, angle)
    source = "ai" if draft else "template"
    if not draft:
        ac = angle_copy(industry, angle, region, company, city, policy)
        draft = {"headline": ac["headline"], "sub": ac["sub"]}
    checks = verify_copy([draft["headline"], draft["sub"]], facts, company, policy)
    # a line the Gate WILL block — so the verification is visible regardless of the AI being on
    blocked = verify_copy([f"The #1 platform for {ind['label'].lower()}, trusted by 10,000 teams."],
                          facts, company, policy)[0]
    ships = all(c["ok"] for c in checks)
    note = ("Drafted by the AI copy agent — every line Gate-verified." if source == "ai"
            else "AI agent off (no ANTHROPIC_API_KEY) — showing the deterministic angle. The Gate still runs.")
    return {"source": source, "headline": draft["headline"], "sub": draft["sub"], "cta": ind["cta"],
            "checks": checks, "blocked_example": blocked, "ships": ships, "note": note, "competitive": False}
