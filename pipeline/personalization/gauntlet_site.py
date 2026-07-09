"""GauntletAI replica — live entry-point + IP + CRM personalization for /gauntlet (+ /dev).

A pixel-faithful mock of gauntletai.com whose copy blocks are personalization SLOTS filled
deterministically from the engine the repo already has:

  • classify_entry() — the four entry channels the funnel catalogues (signals.py lists
    UTM/referrer but live code never parsed them — this implements it): ad (utm_medium ∈
    paid/cpc/ppc/display), email (utm_medium=email, + optional `e=` magic token), search
    (?ref=google|bing|ddg or a search-engine Referer), direct (nothing).
  • scene.detect()/resolve_ip() — the always-on IP layer: network type + tiers 0–3.
  • cohort.match()/by_token() + segments.derive()/pick_archetype() — the known-visitor path
    (login or magic token) → CRM record → archetype → section emphasis + say-level copy.

Surface policy is enforced exactly as the repo defines it: `say` facts (typed/logged-in
identity, declared goal, work-email domain) may be recited; `allude` facts (IP firmographics,
Vector de-anon, HubSpot behavior) only SHAPE copy (industry/region framing, section order);
`hold` facts (modeled income, precise location) never reach the page — the recite variants
appear only on /dev, marked blocked. Every decision lands in a trace entry:
{stage, signals, rule, disposition, output, why}. Deterministic — no LLM, no RNG.
"""
from __future__ import annotations

from pipeline.personalization import cohort as CO
from pipeline.personalization import scene as SC
from pipeline.personalization import segments as SEG

# --------------------------------------------------------------------------- #
# Entry classification — the four channels
# --------------------------------------------------------------------------- #
AD_MEDIUMS = {"paid", "cpc", "ppc", "display"}
SEARCH_REFS = {"google", "bing", "ddg", "duckduckgo"}
SEARCH_HOSTS = ("google.", "bing.com", "duckduckgo.com", "ddg.gg")

CHANNEL_LABELS = {"ad": "Paid ad (UTM)", "email": "Email (UTM)",
                  "search": "Organic search", "direct": "Direct"}


def classify_entry(request) -> dict:
    """UTM + referrer → one of the four entry channels, with the rule that fired.
    Pure function of the request (query params + Referer header) — no network, no state."""
    q = request.query_params
    utm_source = q.get("utm_source", "")
    utm_medium = q.get("utm_medium", "").strip().lower()
    utm_campaign = q.get("utm_campaign", "").strip().lower()
    utm_content = q.get("utm_content", "").strip().lower()
    ref = q.get("ref", "").strip().lower()
    referer = request.headers.get("referer", "")
    token = q.get("e", "").strip()
    person = CO.by_token(token) if token else None

    if utm_medium in AD_MEDIUMS:
        channel = "ad"
        rule = f"utm_medium={utm_medium} ∈ {{paid, cpc, ppc, display}}"
        why = (f"the click carried ad UTMs (source={utm_source or '—'}, "
               f"campaign={utm_campaign or '—'}) — message-match the hero to the campaign")
    elif utm_medium == "email":
        channel = "email"
        rule = "utm_medium=email" + (" + e= magic token" if token else "")
        why = ("the click came from an email we sent" +
               (f" — the magic token identifies {person['vector']['name']} with no login"
                if person else " — warm framing, no identity until they log in"))
    elif ref in SEARCH_REFS or any(h in referer.lower() for h in SEARCH_HOSTS):
        channel = "search"
        rule = (f"?ref={ref} simulates a search referrer" if ref in SEARCH_REFS
                else "Referer header is a search engine")
        why = "search arrivals carry intent but no campaign promise — keep copy intent-neutral"
    else:
        channel = "direct"
        rule = "no UTM, no search referrer"
        why = "nothing about the click tells us anything — the IP layer is the only signal"

    signals = [
        {"label": "utm_source", "value": utm_source or "—"},
        {"label": "utm_medium", "value": utm_medium or "—"},
        {"label": "utm_campaign", "value": utm_campaign or "—"},
        {"label": "utm_content", "value": utm_content or "—"},
        {"label": "ref", "value": ref or "—"},
        {"label": "Referer header", "value": referer or "—"},
        {"label": "e (magic token)", "value": (token[:12] + "…") if token else "—"},
    ]
    return {"channel": channel, "channel_label": CHANNEL_LABELS[channel],
            "utm_source": utm_source, "utm_medium": utm_medium, "utm_campaign": utm_campaign,
            "utm_content": utm_content, "ref": ref, "referer": referer, "token": token,
            "token_person_id": person["id"] if person else None,
            "rule": rule, "why": why, "signals": signals}


def _campaign_intent(campaign: str) -> str | None:
    """Which audience a campaign name message-matches to. Deterministic keyword rule."""
    c = (campaign or "").lower()
    if any(w in c for w in ("catalyst", "cto", "upskill", "team", "hr-", "hiring", "talent", "transform", "roi", "velocity")):
        return "companies"
    if any(w in c for w in ("challenger", "apply", "engineer", "career", "ship")):
        return "individuals"
    return None


# --------------------------------------------------------------------------- #
# X.com ad variants — 9 total = 3 audience segments × 3 copy angles each.
#
# Segments (rows on /ad-lp):
#   cto      — CTO / VP Engineering: hiring AI-native engineers, team transformation
#   engineer — Individual senior engineer: Challenger program, career leap
#   hr       — HR / L&D leader: Catalyst upskilling existing teams
#
# Angles (columns on /ad-lp):
#   cto:      hiring · transform · talent-gap
#   engineer: challenger · career-leap · ship-proof
#   hr:       catalyst · roi · velocity
#
# Each variant carries utm_campaign={segment}-{angle} and utm_content=v01–v09.
# Copy follows docs/research/copy-personalization-research.md: 60–90 words, one idea,
# soft CTA, loss framing where signal-derived, matched-peer social proof, one trigger.
# --------------------------------------------------------------------------- #
AD_SEGMENTS = {
    "cto": {
        "label": "CTO / VP Engineering",
        "subtitle": "Hiring AI-native engineers · team transformation",
        "handle": "GauntletAI",
        "display": "Gauntlet AI",
        "avatar": "CT",
        "accent": "#3b82f6",
    },
    "engineer": {
        "label": "Senior Engineer",
        "subtitle": "Challenger program · career leap",
        "handle": "GauntletAI",
        "display": "Gauntlet AI",
        "avatar": "SE",
        "accent": "#10b981",
    },
    "hr": {
        "label": "HR / L&D Leader",
        "subtitle": "Catalyst upskilling · team velocity",
        "handle": "GauntletAI",
        "display": "Gauntlet AI",
        "avatar": "LD",
        "accent": "#a855f7",
    },
}

AD_ANGLE_LABELS = {
    "cto": ("Hiring signal", "Team transform", "Talent gap"),
    "engineer": ("Challenger", "Career leap", "Ship proof"),
    "hr": ("Catalyst upskill", "L&D ROI", "Team velocity"),
}

_ANGLE_ORDER = {
    "cto": ("hiring", "transform", "talent-gap"),
    "engineer": ("challenger", "career-leap", "ship-proof"),
    "hr": ("catalyst", "roi", "velocity"),
}


def _v(id_, variant_id, segment, angle, angle_label, audience, utm_campaign, *,
       trigger, body, proof, cta_label,
       h1_pre, h1_gold, sub, hero_eyebrow="",
       cta_primary, cta_secondary,
       compare_emphasis, order=None,
       prove_intro=None, challenger_body=None, challenger_hot=False,
       cta_heading=None, cta_sub=None, stat_highlight=None):
    """Build one ad variant dict with paired ad mockup + landing-page overrides."""
    seg = AD_SEGMENTS[segment]
    return {
        "id": id_,
        "variant_id": variant_id,
        "segment": segment,
        "segment_label": seg["label"],
        "angle": angle,
        "angle_label": angle_label,
        "audience": audience,
        "utm_campaign": utm_campaign,
        "utm_source": "x",
        "utm_medium": "paid",
        "ad": {
            "handle": seg["handle"],
            "display": seg["display"],
            "avatar": seg["avatar"],
            "accent": seg["accent"],
            "trigger": trigger,
            "body": body,
            "proof": proof,
            "cta_label": cta_label,
            "text": f"{trigger} {body} {proof}",
        },
        "page": {
            "hero_eyebrow": hero_eyebrow or f"From your X ad · {angle_label}",
            "h1_pre": h1_pre,
            "h1_gold": h1_gold,
            "sub": sub,
            "cta_primary": cta_primary,
            "cta_secondary": cta_secondary,
            "compare_emphasis": compare_emphasis,
            "order": order,
            "prove_intro": prove_intro,
            "challenger_body": challenger_body,
            "challenger_hot": challenger_hot,
            "cta_heading": cta_heading,
            "cta_sub": cta_sub,
            "stat_highlight": stat_highlight,
        },
    }


AD_VARIANTS: list[dict] = [
    # --- CTO / VP Eng (companies · Hire emphasis) ---
    _v("cto-hiring", "v01", "cto", "hiring", "Hiring signal", "companies", "cto-hiring",
       trigger="Saw your team posted three ML engineer roles last month.",
       body=("Usually means you're hiring for skills you can only observe in a 45-minute loop — "
             "while AI pilots sit idle."),
       proof=("Most Series B CTOs tell us the last three AI hires took six months to ramp. "
              "Gauntlet places engineers who've shipped 10+ production apps under 80-hour weeks."),
       cta_label="See how they prove it →",
       hero_eyebrow="You clicked the hiring ad",
       h1_pre="Stop Interviewing for Skills You ", h1_gold= "Can't Observe in 45 Minutes",
       sub=("Gauntlet places engineers whose capability has already been observed across ten weeks "
            "of production pressure — not a whiteboard loop. 5,000+ applicants per cohort; you watch them ship."),
       cta_primary="Hire Proven Talent", cta_secondary="See the Proof Model",
       compare_emphasis="gauntlet",
       prove_intro=("Traditional interviews compress signal into hours. Gauntlet observes execution "
                    "across weeks — the hire track shows you engineers who've already shipped under pressure."),
       cta_heading="Your next AI hire shouldn't be a guess",
       cta_sub="Watch engineers prove it before you sign the offer.",
       stat_highlight=0),
    _v("cto-transform", "v02", "cto", "transform", "Team transform", "companies", "cto-transform",
       trigger="Your Q3 note mentioned doubling the engineering org.",
       body=("When teams scale that fast, the bottleneck isn't models — it's engineers who can "
             "operate AI-first under production load."),
       proof=("Catalyst rewired Northwind's existing team in six weeks — engineers came back building "
              "RAG pipelines and agent workflows, not slide decks."),
       cta_label="Worth a look? →",
       hero_eyebrow="You clicked the transformation ad",
       h1_pre="Your Engineers Ship Features. ", h1_gold= "Catalyst Teaches Them to Ship AI.",
       sub=("A 6-week immersive cohort for the team you already have — real AI systems: RAG pipelines, "
            "agents, workflows, MCP. Because most AI pilots don't have a technology problem, they have a talent problem."),
       cta_primary="Upskill Your Team", cta_secondary="Hire Instead",
       compare_emphasis="catalyst",
       prove_intro=("We train your existing engineers to build AI-native — week after week, under real "
                    "production pressure. Catalyst is the fastest path when hiring isn't the bottleneck."),
       cta_heading="Rewire the team you already have",
       cta_sub="Six weeks. Full-time step-out. Engineers who come back as internal AI champions.",
       stat_highlight=1),
    _v("cto-talent-gap", "v03", "cto", "talent-gap", "Talent gap", "companies", "cto-talent-gap",
       trigger="87% of AI pilots stall — and it's rarely the model.",
       body=("The pattern we hear from CTOs: the technology works, but nobody on the team can "
             "operate it under production pressure."),
       proof=("Gauntlet solves the talent side two ways — place proven engineers (Hire) or rewire "
              "your existing team (Catalyst). Owner and Mainsail Partners already did."),
       cta_label="Open to the breakdown? →",
       hero_eyebrow="You clicked the talent-gap ad",
       h1_pre="Most AI Pilots Stall on ", h1_gold= "Talent — Not Technology",
       sub=("You don't have a model problem. You have a capability problem. Hire engineers who've "
            "already proven it under ten weeks of pressure — or upskill the team you already trust with Catalyst."),
       cta_primary="Fix the Talent Gap", cta_secondary="Compare Hire vs Catalyst",
       compare_emphasis="catalyst",
       order=["hero", "compare", "prove", "numbers", "challenger", "cta"],
       prove_intro=("Two paths, same proof model: sustained observation under production pressure. "
                    "Pick hire if you need net-new capability; pick Catalyst if your engineers are ready to rewire."),
       cta_heading="The pilot works. The team doesn't — yet.",
       cta_sub="Hire proven engineers or upskill the ones you already have.",
       stat_highlight=2),
    # --- Senior Engineer (individuals · Challenger emphasis) ---
    _v("engineer-challenger", "v04", "engineer", "challenger", "Challenger", "individuals", "engineer-challenger",
       trigger="5,000+ engineers apply per Gauntlet cohort.",
       body=("Ten weeks, full-time, everything covered — you prove you can ship AI systems under "
             "80-hour weeks, not interview composure."),
       proof=("Challengers who complete the program ship 10+ production apps. The selection rate "
              "makes the credential mean something."),
       cta_label="Worth applying? →",
       hero_eyebrow="You clicked the Challenger ad",
       h1_pre="10 Weeks to Prove You're an ", h1_gold= "AI-First Engineer",
       sub=("Train as a Gauntlet Challenger — full-time, everything covered. Every week requires "
            "shipped code and working systems. This isn't preparation for evaluation. It is the evaluation."),
       cta_primary="Become a Challenger →", cta_secondary="See How We Prove It",
       compare_emphasis="gauntlet",
       challenger_hot=True,
       challenger_body=("Apply to train as a Gauntlet Challenger — 10 weeks, full-time, everything covered. "
                        "5,000+ applicants per cohort. Standards rise every week."),
       cta_heading="Think this is you?",
       cta_sub="Most engineers wait. Challengers ship.",
       stat_highlight=0),
    _v("engineer-career-leap", "v05", "engineer", "career-leap", "Career leap", "individuals", "engineer-career-leap",
       trigger="Senior engineers who made the AI leap tell us the same thing.",
       body=("The difference wasn't another cert — it was ten weeks of sustained observation "
             "under real production pressure."),
       proof=("One Challenger shipped 12 production systems in training. Traditional interviews "
              "would have missed every signal that mattered."),
       cta_label="Open to the path? →",
       hero_eyebrow="You clicked the career-leap ad",
       h1_pre="The Career Leap Senior Engineers ", h1_gold= "Regret Waiting On",
       sub=("Gauntlet Challenger is a 10-week immersive cohort where you build RAG pipelines, agents, "
            "and workflows — then demo them live under scrutiny. Prove the leap, don't pitch it."),
       cta_primary="Apply to Challenger →", cta_secondary="See Alumni Outcomes",
       compare_emphasis="gauntlet",
       order=["hero", "challenger", "prove", "numbers", "compare", "cta"],
       challenger_hot=True,
       prove_intro=("You've shipped before — this is how we prove you can ship AI-native. Weekly live "
                    "reviews, escalating complexity, sustained observation across ten weeks."),
       cta_heading="Stop waiting for permission to go AI-first",
       cta_sub="Ten weeks. Full-time. Everything covered. Prove it under pressure.",
       stat_highlight=1),
    _v("engineer-ship-proof", "v06", "engineer", "ship-proof", "Ship proof", "individuals", "engineer-ship-proof",
       trigger="Traditional interviews compress signal into hours.",
       body=("Gauntlet observes execution across ten weeks — patterns that matter only become "
             "visible over time."),
       proof=("Every Challenger ships 10+ production systems during training. Weekly live reviews "
              "under scrutiny, not whiteboard theater."),
       cta_label="See the proof model →",
       hero_eyebrow="You clicked the ship-proof ad",
       h1_pre="Interviews Show Composure. ", h1_gold= "Gauntlet Shows Execution.",
       sub=("Ten weeks of shipped code, deployed systems, and live demos under pressure. "
            "The Challenger program is the evaluation — not preparation for one."),
       cta_primary="Prove You Can Ship →", cta_secondary="How Selection Works",
       compare_emphasis="gauntlet",
       prove_intro=("Production only. Weekly live reviews. Escalating complexity. "
                    "By the end you've shown how you adapt — not just what you can do on a good day."),
       cta_heading="Show them you ship — don't tell them",
       cta_sub="Ten weeks of production pressure. One credential that means something.",
       stat_highlight=0),
    # --- HR / L&D (companies · Catalyst emphasis) ---
    _v("hr-catalyst", "v07", "hr", "catalyst", "Catalyst upskill", "companies", "hr-catalyst",
       trigger="Your L&D budget buys courses. Catalyst buys engineers who come back different.",
       body=("Six weeks, full-time step-out — your engineers build real RAG pipelines and agent "
             "workflows, not slide decks."),
       proof=("HR leaders at 200–500 person tech shops say upskilling wins when engineers ship "
              "production AI systems tied to business ROI."),
       cta_label="Worth sending the overview? →",
       hero_eyebrow="You clicked the Catalyst ad",
       h1_pre="Your L&D Budget Buys Courses. ", h1_gold= "Catalyst Buys AI Champions.",
       sub=("A 6-week immersive cohort for engineers you select — real AI systems, production-grade "
            "capstone tied to business ROI. They come back as internal AI leads, not certificate holders."),
       cta_primary="Upskill Your Team", cta_secondary="See Catalyst Details",
       compare_emphasis="catalyst",
       prove_intro=("Catalyst rewires the team you already have — engineers step out full-time for six weeks "
                    "and return building AI-native systems your org can actually deploy."),
       cta_heading="Turn your L&D line item into AI capability",
       cta_sub="Per-employee fee. Engineers you select. Champions you keep.",
       stat_highlight=1),
    _v("hr-roi", "v08", "hr", "roi", "L&D ROI", "companies", "hr-roi",
       trigger="Training that doesn't change how engineers operate is shelfware.",
       body=("Most L&D leaders tell us the same gap: courses complete, but nothing in production moves."),
       proof=("Northwind cut internal AI ramp from 14 weeks to 6 with Catalyst — engineers returned "
              "shipping RAG pipelines, not requesting more budget."),
       cta_label="Open to the ROI breakdown? →",
       hero_eyebrow="You clicked the L&D ROI ad",
       h1_pre="Shelfware Training vs. ", h1_gold= "Engineers Who Ship AI",
       sub=("Catalyst measures success by capstone completion tied to business ROI — not attendance "
            "or quiz scores. Six weeks, full-time step-out, production-grade systems your team deploys."),
       cta_primary="See Catalyst ROI", cta_secondary="Talk to Our Team",
       compare_emphasis="catalyst",
       order=["hero", "compare", "numbers", "prove", "challenger", "cta"],
       prove_intro=("Validation isn't a certificate — it's a successful capstone project completion "
                    "your business can point to. That's the ROI L&D leaders actually report."),
       cta_heading="Stop funding training nobody uses",
       cta_sub="Catalyst engineers come back shipping — not requesting the next course.",
       stat_highlight=2),
    _v("hr-velocity", "v09", "hr", "velocity", "Team velocity", "companies", "hr-velocity",
       trigger="Upskilling wins when engineers build RAG pipelines — not watch them.",
       body=("HR leaders at mid-market tech shops say velocity stalls when training stays theoretical."),
       proof=("Catalyst engineers build real AI systems: agents, workflows, MCP integrations. "
              "August 17 cohort — engineers you select, champions you keep."),
       cta_label="Worth a 2-line reply? →",
       hero_eyebrow="You clicked the velocity ad",
       h1_pre="Upskilling That Changes ", h1_gold= "How Engineers Operate",
       sub=("Catalyst is a 6-week immersive cohort — your engineers step out full-time and return "
            "building AI systems your org can deploy next quarter. Not next year."),
       cta_primary="Accelerate Your Team", cta_secondary="Compare Programs",
       compare_emphasis="catalyst",
       prove_intro=("Full-time step-out means velocity — six weeks from capable engineer to internal "
                    "AI champion shipping production systems. That's the upskill L&D was meant to buy."),
       cta_heading="Velocity beats volume in L&D",
       cta_sub="Six weeks. Real systems. Engineers who come back different.",
       stat_highlight=1),
]

AD_BY_CAMPAIGN = {v["utm_campaign"]: v for v in AD_VARIANTS}
AD_BY_VARIANT_ID = {v["variant_id"]: v for v in AD_VARIANTS}


def resolve_ad_variant(entry: dict) -> dict | None:
    """Map UTM campaign + content to one of the 9 catalogued X.com ad variants."""
    if entry.get("channel") != "ad":
        return None
    content = (entry.get("utm_content") or "").strip().lower()
    if content and content in AD_BY_VARIANT_ID:
        return AD_BY_VARIANT_ID[content]
    campaign = (entry.get("utm_campaign") or "").strip().lower()
    if campaign and campaign in AD_BY_CAMPAIGN:
        return AD_BY_CAMPAIGN[campaign]
    return None


def variant_landing_url(variant: dict, page_path: str = "/gauntlet") -> str:
    """Full landing-page URL with the variant's UTM params."""
    q = (f"utm_source={variant['utm_source']}&utm_medium={variant['utm_medium']}"
         f"&utm_campaign={variant['utm_campaign']}&utm_content={variant['variant_id']}")
    return f"{page_path}?{q}"


def ad_grid_rows() -> list[dict]:
    """3×3 grid data for /ad-lp: rows = segments, cols = angles."""
    rows = []
    for seg_key, seg in AD_SEGMENTS.items():
        by_angle = {v["angle"]: v for v in AD_VARIANTS if v["segment"] == seg_key}
        ordered = [by_angle[a] for a in _ANGLE_ORDER[seg_key]]
        rows.append({
            "segment": seg_key,
            "segment_info": seg,
            "angle_labels": AD_ANGLE_LABELS[seg_key],
            "variants": ordered,
        })
    return rows


def generic_hero_headline() -> str:
    return GENERIC["hero"]["h1_pre"] + GENERIC["hero"]["h1_gold"]


def variant_hero_headline(variant: dict) -> str:
    p = variant["page"]
    return p["h1_pre"] + p["h1_gold"]

# --------------------------------------------------------------------------- #
# The generic page — the real gauntletai.com copy (captured 2026-07-09).
# These are GauntletAI's own published claims, replicated verbatim; nothing invented.
# --------------------------------------------------------------------------- #
GENERIC = {
    "hero": {
        "eyebrow": "",
        "h1_pre": "Your Fastest Path to Become ", "h1_gold": "AI-First",
        "sub": ("Gauntlet transforms engineers into AI-first operators because most AI pilots "
                "don't have a technology problem, they have a talent problem."),
        "cta_primary": "Hire Proven Talent", "cta_secondary": "Upskill Your Team",
    },
    "prove": {
        "h_pre": "How We Prove They ", "h_gold": "Can Ship",
        "intro": ("We can train your existing team to build AI-native or place engineers who've "
                  "already proven it, week after week, under real production pressure."),
    },
    "challenger": {
        "eyebrow": "For Individual Engineers", "heading": "Think This Is You?",
        "body": "Apply to train as a Gauntlet Challenger — 10 weeks, full-time, everything covered.",
        "cta": "Become a Challenger →",
    },
    "cta": {
        "heading": "Go all-in on AI",
        "sub": "Most AI pilots stall. Gauntlet engineers ship.",
        "cta_primary": "Hire AI-First Engineers", "cta_secondary": "Upskill Your Team",
    },
}

PROVE_CARDS = [
    ("Production Only", "Every week requires shipped code and working systems. This isn't "
                        "preparation for evaluation. It is the evaluation."),
    ("Weekly Live Reviews", "Engineers demo deployed systems under scrutiny. You observe "
                            "reasoning, decision-making, and response to pressure, not "
                            "interview composure."),
    ("Sustained Observation", "Traditional interviews compress signal into hours. Our programs "
                              "observe execution across weeks. Patterns that matter only "
                              "become visible over time."),
    ("Escalating Complexity", "Standards rise every week. By the end you've seen how engineers "
                              "adapt, not just what they can do on a good day."),
]

COMPARE_ROWS = [
    ("Format", "10-week immersive cohort", "6-week immersive cohort"),
    ("Best for", "Teams that need to hire engineers whose capability has already been observed "
                 "under sustained pressure.",
     "Teams whose engineers are capable but operating inside environments that constrain how "
     "much they can structurally change."),
    ("Selection", "5,000+ applicants per cohort", "Engineers you select"),
    ("Weekly hours", "80–100 hrs/week", "Full-time step-out"),
    ("What they build", "10+ shipped apps across web, mobile, and AI systems",
     "Real AI systems: RAG pipelines, agents, workflows, MCP"),
    ("Capstone", "End-to-end AI system deployment", "Production-grade capstone tied to business ROI"),
    ("Validation", "Demo day live presentation", "Successful capstone project completion"),
    ("Pricing", "Placement fee (credits pre-purchased)", "Per-employee fee"),
    ("What you get back", "Engineers who have shipped under sustained production pressure for "
                          "ten weeks.",
     "Engineers who come back as internal AI champions, and internal AI leads."),
    ("Next cohort", "September 14", "August 17"),
]

NUMBERS = [("500+", "Apps shipped during training"),
           ("10+", "Production systems per engineer"),
           ("20,000+", "Applicants to date")]

TRUSTED_BY = ["Owner", "Mainsail Partners", "NEXA Equity", "Nerdy Live+AI", "Bissell"]

# real-site section order — reorders per audience, structure never changes
DEFAULT_ORDER = ["hero", "prove", "challenger", "compare", "numbers", "cta"]
ORDER_BY_AUDIENCE = {
    "companies": ["hero", "prove", "compare", "numbers", "challenger", "cta"],
    "individuals": ["hero", "challenger", "prove", "compare", "numbers", "cta"],
    "neutral": DEFAULT_ORDER,
}


# --------------------------------------------------------------------------- #
# The builder
# --------------------------------------------------------------------------- #
def _resolve_visitor(request, ip_override: str) -> tuple[dict, bool]:
    """The always-on IP layer: the visitor's own IP, or an entered ?ip= (like /showcase)."""
    det = SC.detect(request)
    if ip_override:
        rv = SC.resolve_ip(ip_override)
        rv["request_signals"] = det.get("request_signals", [])
        return rv, True
    return det, False


def _identity(email: str | None, entry: dict) -> dict | None:
    """Who the visitor is, if anyone: login email (say) or the email magic token (say —
    the token was minted into a link we sent them). Cohort hit → the full CRM record;
    unknown work email → first-party domain resolution (resolve_email, offline-safe)."""
    via = None
    person = None
    if email:
        person, via = CO.match(email), "login"
    if person is None and entry.get("token_person_id"):
        person, via = CO.BY_ID[entry["token_person_id"]], "magic token"
        email = person["email"]
    if person:
        v = CO.view(person)
        segs = SEG.derive(v)
        arch = SEG.pick_archetype(v, segs)
        return {"kind": "cohort", "via": via, "email": person["email"], "view": v,
                "first": v["name"].split()[0], "segments": segs, "archetype": arch,
                "crm": person}
    if email:
        res = SC.resolve_email(email)
        return {"kind": "resolved", "via": "login", "email": email, "view": None,
                "first": None, "segments": None, "archetype": None, "resolved": res}
    return None


def _audience(entry: dict, det: dict, ident: dict | None,
              variant: dict | None = None) -> tuple[str, str, str]:
    """Route the page to an audience: companies (Hire/Catalyst emphasis) vs individuals
    (Challenger emphasis). Returns (audience, rule, why)."""
    if variant:
        aud = variant["audience"]
        return (aud,
                f"ad variant {variant['id']} (utm_campaign={variant['utm_campaign']})",
                f"the X.com ad promised {variant['angle_label']} to {variant['segment_label']} — "
                "message-match the hero, CTAs, and table emphasis to that promise")
    intent = _campaign_intent(entry.get("utm_campaign"))
    if intent:
        return intent, f"utm_campaign={entry['utm_campaign']} message-matches {intent}", \
            "the campaign promise decides the emphasis — B2B campaigns lead with hire/upskill, " \
            "challenger campaigns lead with the individual track"
    if ident and ident["kind"] == "cohort":
        li = ident["view"]["linkedin"]
        goal = (ident["view"]["declared"].get("goal") or "").lower()
        if li.get("seniority") == "exec" or "team" in goal:
            return "companies", f"CRM: seniority={li.get('seniority')}, goal mentions team", \
                "a senior leader hiring for a team gets the companies framing"
        return "individuals", f"CRM: seniority={li.get('seniority')} — an individual track", \
            "the CRM record describes an individual engineer/switcher, not a buyer"
    if ident and ident["kind"] == "resolved" and ident["resolved"].get("company"):
        return "companies", f"work-email domain → {ident['resolved']['company']}", \
            "a work email identifies a company — B2B framing"
    net = det.get("network_type", "")
    if net in ("corporate", "corporate (via VPN)"):
        return "companies", f"network type = {net}", \
            "a corporate netblock is a B2B signal — emphasize Hire/Catalyst"
    if net in ("residential", "consumer ISP", "mobile"):
        return "individuals", f"network type = {net}", \
            "a residential/mobile visitor is likelier an individual engineer — emphasize Challenger"
    return "neutral", f"network type = {net or 'unknown'} — no audience signal", \
        "VPN/hosting/unknown networks say nothing about who's visiting — the real-site default ships"


def _ind_label(det: dict) -> str:
    key = det.get("industry")
    return SC.BY_KEY[key]["label"].lower() if key else ""


def build_page(request, email: str | None = None, overrides: dict | None = None) -> dict:
    """Compose entry channel × IP tier × identity/CRM into the replica's page contract +
    the full decision trace. Deterministic: same inputs → same page, same trace."""
    overrides = overrides or {}
    q = request.query_params
    ip_override = overrides.get("ip", q.get("ip", ""))

    entry = classify_entry(request)
    det, ip_forced = _resolve_visitor(request, ip_override)
    ident = _identity(email, entry)
    ad_variant = resolve_ad_variant(entry)
    audience, aud_rule, aud_why = _audience(entry, det, ident, ad_variant)

    tier, tier_label = det.get("tier", 0), det.get("tier_label", SC.TIER_LABELS[0])
    region, industry = det.get("region"), _ind_label(det)
    company, city = det.get("company"), det.get("city")

    trace: list[dict] = []

    def t(stage, signals, rule, disposition, output, why):
        trace.append({"stage": stage, "signals": signals, "rule": rule,
                      "disposition": disposition, "output": output, "why": why})

    t("Entry classify", [s["label"] + "=" + s["value"] for s in entry["signals"] if s["value"] != "—"] or ["(none)"],
      entry["rule"], "observed", f"channel = {entry['channel_label']}", entry["why"])

    if ad_variant:
        t("Ad variant resolve",
          [f"utm_campaign={ad_variant['utm_campaign']}", f"utm_content={ad_variant['variant_id']}",
           f"segment={ad_variant['segment']}", f"angle={ad_variant['angle']}"],
          "AD_BY_CAMPAIGN / AD_BY_VARIANT_ID lookup",
          "observed",
          f"variant = {ad_variant['id']} · {ad_variant['segment_label']} × {ad_variant['angle_label']}",
          "the paid click carried a catalogued X.com campaign — every copy slot message-matches this variant")

    ip_sig = [f"ip={det.get('ip') or '—'}", f"network={det.get('network_type', '—')}"]
    if region:
        ip_sig.append(f"region={region}")
    if company:
        ip_sig.append(f"company={company}")
    if industry:
        ip_sig.append(f"industry={industry}")
    t("IP resolve + classify", ip_sig,
      "reverse-IP (ip-api) → network flags → deterministic router (scene._classify)",
      "allude", f"network {det.get('network_type', 'private / unreachable')}",
      det.get("reason") or "corporate IP with a resolved sector — firmographic copy may ship (allude framing only)")

    conf = det.get("confidence", {"location": "none", "company": "none", "industry": "none"})
    t("Tier route", [f"confidence: location={conf['location']} · company={conf['company']} · industry={conf['industry']}"],
      "industry resolved → 2 · geo only → 1 · nothing usable → 0 (scene.TIER_LABELS)",
      "observed", f"tier {tier} · {tier_label}",
      "the tier gates which copy path runs — never what we recite")

    if ident and ident["kind"] == "cohort":
        v = ident["view"]
        t("Identity", [f"{ident['via']} → {ident['email']}"],
          "cohort.match(email)" if ident["via"] == "login" else "cohort.by_token(e)",
          "say", f"{v['name']} — CRM record found (HubSpot {v['hubspot']['lifecycle']}, "
                 f"score {v['hubspot']['lead_score']}, {v['hubspot']['visits']} visits)",
          "they identified themselves — name and declared facts unlock at say level; "
          "Vector/Clay enrichment stays allude/hold")
        t("Segments → archetype",
          [f"{fam}: " + ", ".join(s["label"] for s in d["segments"]) for fam, d in ident["segments"].items()],
          "segments.derive() → pick_archetype()", "allude",
          f"archetype = {ident['archetype']['label']} ({ident['archetype']['reason']})",
          "behavioral + enriched segments choose emphasis and section order — they are never recited")
    elif ident and ident["kind"] == "resolved":
        r = ident["resolved"]
        t("Identity", [f"login → {ident['email']}"], "resolve_email(): domain → company (first-party)",
          "say", f"company = {r.get('company') or '—'} (tier {r.get('tier', 0)})",
          r.get("reason") or "a work email is a declared identity — the domain names the company, say level")
    else:
        t("Identity", ["(no login, no token)"], "cohort.match / by_token", "hold",
          "anonymous", "no identity offered — nothing personal may be said")

    t("Audience route", [aud_rule], "campaign intent > CRM > work-email domain > network type",
      "allude", f"audience = {audience}", aud_why)

    # ------------------------------------------------------------------ #
    # Copy slots. Each slot records generic vs shipped (+ the say variant the policy blocks).
    # ------------------------------------------------------------------ #
    diff: list[dict] = []

    def slot(sid, label, generic, shipped, source, policy, blocked_say=None, why=""):
        diff.append({"slot": sid, "label": label, "generic": generic, "shipped": shipped,
                     "changed": generic != shipped, "source": source, "policy": policy,
                     "blocked_say": blocked_say, "why": why})
        return shipped

    hero = dict(GENERIC["hero"])
    prove = dict(GENERIC["prove"])
    challenger = dict(GENERIC["challenger"])
    cta = dict(GENERIC["cta"])

    # --- hero eyebrow: the one always-on personalization line ---------------
    eyebrow, eyebrow_src, eyebrow_pol = "", "—", "say"
    blocked_eyebrow = None
    if ident and ident["kind"] == "cohort":
        eyebrow = f"Welcome back, {ident['first']}"
        eyebrow_src, eyebrow_pol = f"identity via {ident['via']} (say)", "say"
        v = ident["view"]
        li = v["linkedin"]
        blocked_eyebrow = (f"{v['name']} — {li['title']} at {li['company']} — we de-anonymized "
                           "your visit") if li.get("company") not in ("—", "", None) else None
    elif ident and ident["kind"] == "resolved" and ident["resolved"].get("company"):
        eyebrow = f"For your team at {ident['resolved']['company']}"
        eyebrow_src, eyebrow_pol = "work-email domain (first-party, say)", "say"
    elif tier >= 2 and industry:
        eyebrow = f"For {industry} engineering teams" + (f" in {region}" if region else "")
        eyebrow_src, eyebrow_pol = "reverse-IP firmographic (allude — shapes, never recites)", "allude"
        blocked_eyebrow = f"{company} — we see your {industry} team in {city or region}"
    elif tier == 1 and region:
        eyebrow = f"Serving engineering teams across {region}"
        eyebrow_src, eyebrow_pol = "geo-IP region (allude)", "allude"
    elif entry["channel"] == "email":
        eyebrow = "Straight from your inbox — welcome back"
        eyebrow_src, eyebrow_pol = "email UTM (first-party send)", "allude"
    elif ad_variant:
        eyebrow = ad_variant["page"]["hero_eyebrow"]
        eyebrow_src = f"ad variant {ad_variant['id']} message-match"
        eyebrow_pol = "allude"
    hero["eyebrow"] = slot("hero_eyebrow", "Hero eyebrow", "", eyebrow, eyebrow_src, eyebrow_pol,
                           blocked_say=blocked_eyebrow,
                           why="the always-on line: say-level identity beats first-party domain "
                               "beats IP firmographics beats geo")

    # --- hero headline + sub: message-match to the campaign / archetype -----
    h1_pre, h1_gold, sub = hero["h1_pre"], hero["h1_gold"], hero["sub"]
    h_src, h_pol = "—", "say"
    if ad_variant:
        vp = ad_variant["page"]
        h1_pre, h1_gold, sub = vp["h1_pre"], vp["h1_gold"], vp["sub"]
        h_src = f"ad variant {ad_variant['id']} (utm_campaign={ad_variant['utm_campaign']})"
        h_pol = "allude"
    elif entry["channel"] == "ad" and _campaign_intent(entry["utm_campaign"]) == "companies":
        h1_pre, h1_gold = "Rewire Your Engineers to Be ", "AI-First"
        sub = ("Catalyst rewires the team you already have — a 6-week immersive cohort, "
               "because most AI pilots don't have a technology problem, they have a talent problem.")
        h_src, h_pol = f"ad message-match (utm_campaign={entry['utm_campaign']})", "allude"
    elif entry["channel"] == "ad" and _campaign_intent(entry["utm_campaign"]) == "individuals":
        h1_pre, h1_gold = "Your Fastest Path to Become an ", "AI-First Engineer"
        sub = ("Train as a Gauntlet Challenger — 10 weeks, full-time, everything covered. "
               "Prove you can ship, week after week, under real production pressure.")
        h_src, h_pol = f"ad message-match (utm_campaign={entry['utm_campaign']})", "allude"
    elif ident and ident["kind"] == "cohort":
        goal = ident["view"]["declared"].get("goal", "")
        if goal:
            sub = f"You told us you want to {goal} — here's the fastest path."
            h_src, h_pol = "HubSpot form · interest reason (declared → say)", "say"
        else:
            arch = ident["archetype"]
            sub = f"Tuned for {arch['for']} — " + hero["sub"][0].lower() + hero["sub"][1:]
            h_src, h_pol = f"archetype {arch['label']} (modeled → allude)", "allude"
    hero["h1_pre"], hero["h1_gold"] = h1_pre, h1_gold
    hero["sub"] = slot("hero_sub", "Hero headline + sub", GENERIC["hero"]["sub"], sub, h_src, h_pol,
                       blocked_say=(f"Your modeled income is {ident['view']['deep']['income_band']} — "
                                    "we pre-picked a payment plan"
                                    if ident and ident["kind"] == "cohort"
                                    and ident["view"]["deep"].get("income_band") else None),
                       why="ad clicks message-match the campaign promise; a declared goal may be "
                           "recited verbatim (say); modeled income is hold — never shipped")
    diff[-1]["generic"] = GENERIC["hero"]["h1_pre"] + GENERIC["hero"]["h1_gold"] + " · " + GENERIC["hero"]["sub"]
    diff[-1]["shipped"] = h1_pre + h1_gold + " · " + sub
    diff[-1]["changed"] = diff[-1]["generic"] != diff[-1]["shipped"]

    # --- hero CTAs: primary/secondary order follows the audience ------------
    ctas = {"companies": ("Hire Proven Talent", "Upskill Your Team"),
            "individuals": ("Become a Challenger →", "Hire Proven Talent"),
            "neutral": ("Hire Proven Talent", "Upskill Your Team")}[audience]
    if ad_variant:
        vp = ad_variant["page"]
        ctas = (vp["cta_primary"], vp["cta_secondary"])
    elif entry["channel"] == "ad" and _campaign_intent(entry["utm_campaign"]) == "companies":
        ctas = ("Upskill Your Team", "Hire Proven Talent")
    if ident and ident["kind"] == "cohort":
        ctas = (ident["archetype"]["cta"], ctas[0] if ctas[0] != ident["archetype"]["cta"] else ctas[1])
    hero["cta_primary"], hero["cta_secondary"] = ctas
    slot("hero_cta", "Hero CTAs",
         GENERIC["hero"]["cta_primary"] + " / " + GENERIC["hero"]["cta_secondary"],
         ctas[0] + " / " + ctas[1],
         ("archetype CTA (CRM)" if ident and ident["kind"] == "cohort" else f"audience = {audience}"),
         "allude", why="emphasis only — both paths stay on the page")

    # --- prove intro: firmographic allusion ---------------------------------
    intro = prove["intro"]
    p_src, p_pol = "—", "say"
    if ad_variant and ad_variant["page"].get("prove_intro"):
        intro = ad_variant["page"]["prove_intro"]
        p_src = f"ad variant {ad_variant['id']} message-match"
        p_pol = "allude"
    elif tier >= 2 and industry:
        intro = (f"We can train your existing {industry} engineers to build AI-native — or place "
                 "engineers who've already proven it, week after week, under real production pressure.")
        p_src, p_pol = "reverse-IP industry (allude)", "allude"
    elif ident and ident["kind"] == "cohort" and ident["view"]["linkedin"].get("technical"):
        intro = (GENERIC["prove"]["intro"] + " You've shipped before — this is how we prove it.")
        p_src, p_pol = "Clay technical flag (enriched → allude)", "allude"
    prove["intro"] = slot("prove_intro", "\u201cHow We Prove\u201d intro", GENERIC["prove"]["intro"], intro,
                          p_src, p_pol,
                          blocked_say=(f"{company}'s stack could use this" if company else None),
                          why="industry may shape the frame (allude); the company name may not be recited")

    # --- challenger callout: emphasis + warm body for known switchers -------
    ch_body = challenger["body"]
    ch_src, ch_pol = "—", "say"
    if ad_variant and ad_variant["page"].get("challenger_body"):
        ch_body = ad_variant["page"]["challenger_body"]
        ch_src = f"ad variant {ad_variant['id']} message-match"
        ch_pol = "allude"
    elif ident and ident["kind"] == "cohort" and ident["archetype"]["id"] in ("cost_confident", "outcomes_first", "fast_track"):
        arch = ident["archetype"]
        ch_body = (GENERIC["challenger"]["body"] + f" Built for {arch['for']}.")
        ch_src, ch_pol = f"archetype {arch['label']} (modeled → allude)", "allude"
    challenger["body"] = slot("challenger_body", "Challenger callout", GENERIC["challenger"]["body"],
                              ch_body, ch_src, ch_pol,
                              why="the archetype may add a framing line; the segment itself is never named")
    challenger["emphasis"] = (
        ad_variant["page"].get("challenger_hot", False) if ad_variant
        else audience == "individuals"
    )

    # --- comparison table: column emphasis follows the audience -------------
    compare_emphasis = {"companies": "catalyst", "individuals": "gauntlet", "neutral": None}[audience]
    if ad_variant:
        compare_emphasis = ad_variant["page"]["compare_emphasis"]
    elif entry["channel"] == "ad" and _campaign_intent(entry["utm_campaign"]) == "companies":
        compare_emphasis = "catalyst"
    slot("compare_emphasis", "Comparison table emphasis", "none (equal columns)",
         compare_emphasis or "none (equal columns)",
         (f"ad variant {ad_variant['id']}" if ad_variant else f"audience = {audience}"),
         "allude",
         why="emphasis highlights a column — the table's facts are identical for everyone")

    # --- numbers: stat order may shift per ad variant -----------------------
    stats = list(NUMBERS)
    if ad_variant and ad_variant["page"].get("stat_highlight") is not None:
        hi = ad_variant["page"]["stat_highlight"]
        stats = [NUMBERS[hi]] + [s for i, s in enumerate(NUMBERS) if i != hi]
        slot("numbers_order", "Stats emphasis order",
             " · ".join(n[0] for n in NUMBERS),
             " · ".join(n[0] for n in stats),
             f"ad variant {ad_variant['id']} — lead with stat {hi + 1}",
             "allude", why="reorder highlights the stat that matches the ad promise")

    # --- final CTA -----------------------------------------------------------
    f_head, f_sub = cta["heading"], cta["sub"]
    f_src, f_pol = "—", "say"
    if ad_variant and ad_variant["page"].get("cta_heading"):
        f_head = ad_variant["page"]["cta_heading"]
        f_sub = ad_variant["page"].get("cta_sub") or cta["sub"]
        f_src = f"ad variant {ad_variant['id']} message-match"
        f_pol = "allude"
    elif ident and ident["kind"] == "cohort" and ident["archetype"]["id"] == "welcome_back":
        f_head, f_sub = "Pick up where you left off", \
            "Your progress is saved — the next step is waiting."
        f_src, f_pol = "HubSpot past-customer (first-party → allude)", "allude"
    elif ident and ident["kind"] == "cohort" and ident["view"]["hubspot"].get("abandoned"):
        f_head, f_sub = "Finish what you started", \
            "Your application is most of the way there — the next cohort is filling up."
        f_src, f_pol = "HubSpot abandoned action (behavioral → allude)", "allude"
    elif audience == "individuals":
        f_sub = "Most engineers wait. Challengers ship."
    cta["heading"], cta["sub"] = f_head, f_sub
    slot("final_cta", "Final CTA block", GENERIC["cta"]["heading"] + " · " + GENERIC["cta"]["sub"],
         f_head + " · " + f_sub, f_src, f_pol,
         blocked_say=(f"You bailed at the {ident['view']['hubspot']['abandoned']} on "
                      f"{ident['view']['hubspot']['visits']} visits — go back"
                      if ident and ident["kind"] == "cohort" and ident["view"]["hubspot"].get("abandoned") else None),
         why="behavioral facts steer the close but are alluded to, never itemized")

    order = (ad_variant["page"].get("order") if ad_variant and ad_variant["page"].get("order")
             else ORDER_BY_AUDIENCE[audience])
    t("Surface policy", [f"{d['slot']}: {d['policy']}" for d in diff],
      "say = recite · allude = shape only · hold = never ships (docs/04-workflow)",
      "mixed", f"{sum(1 for d in diff if d['changed'])} of {len(diff)} slots personalized",
      "every personalized slot carries its source + policy; the say-level recite variants are "
      "blocked and appear only on /dev")
    t("Compose", [f"order = {' → '.join(order)}"],
      f"section order for audience = {audience}", "allude",
      "same sections, same facts — only emphasis and order move",
      "the structure is identical before and after login; personalization never adds or removes a claim")

    ledger = _ledger(entry, det, ident)
    login_state = bool(ident and ident.get("via") == "login")
    return {
        "entry": entry, "det": det, "ip_forced": ip_forced, "identity": ident,
        "audience": audience, "audience_rule": aud_rule,
        "tier": tier, "tier_label": tier_label, "confidence": conf,
        "sections": {"hero": hero, "prove": {**prove, "cards": PROVE_CARDS},
                     "challenger": challenger,
                     "compare": {"rows": COMPARE_ROWS, "emphasis": compare_emphasis},
                     "numbers": {"stats": stats, "trusted": TRUSTED_BY},
                     "cta": cta},
        "order": order,
        "nav": {"login_state": login_state,
                "login_email": ident["email"] if ident else "",
                "first": ident["first"] if ident and ident.get("first") else "",
                "known": bool(ident),
                "ad_lp": None},
        "login_state": login_state,
        "ad_variant": ad_variant,
        "trace": trace, "copy_diff": diff, "ledger": ledger,
    }


# --------------------------------------------------------------------------- #
# Signal ledger for /dev — source · vendor · tier · disposition
# --------------------------------------------------------------------------- #
_DISPOSITION = {"say": "said", "allude": "steer", "hold": "held", "observed": "observed"}


def _ledger(entry: dict, det: dict, ident: dict | None) -> list[dict]:
    rows: list[dict] = []

    def add(label, value, source, vendor, policy):
        rows.append({"label": label, "value": value if value not in (None, "") else "—",
                     "source": source, "vendor": vendor, "policy": policy,
                     "disposition": _DISPOSITION.get(policy, policy)})

    add("Entry channel", entry["channel_label"], "observed", "UTM / Referer parse", "observed")
    for s in entry["signals"]:
        if s["value"] != "—":
            add(s["label"], s["value"], "observed", "query string / Referer header", "allude")
    for c in det.get("captured", []):
        add(c["label"], c["value"], "observed", "ip-api.com" + (" → PDL" if c["group"] == "resolved" else ""),
            c["policy"])
    for c in det.get("request_signals", []):
        add(c["label"], c["value"], "observed", "HTTP headers", c["policy"])
    if ident and ident["kind"] == "cohort":
        raw = ident["crm"]
        v, hs, cl = raw["vector"], raw["hubspot"], raw["clay"]
        add("Email", ident["email"], "declared", f"{ident['via']}", "say")
        add("Name", v["name"], "declared" if ident["via"] == "login" else "first_party",
            "login identity", "say")
        add("Vector — title / company", f"{v['job_title']} · {v['company']}",
            "first_party", "Vector de-anonymization", "allude")
        add("HubSpot — lifecycle / score", f"{hs['lifecycle']} · score {hs['lead_score']} · {hs['visits']} visits",
            "first_party", "HubSpot CRM", "allude")
        if hs.get("submitted") and hs.get("interest_reason"):
            add("Declared goal", f"\u201c{hs['interest_reason']}\u201d", "declared", "HubSpot form", "say")
        if hs.get("abandoned"):
            add("Abandoned action", hs["abandoned"], "first_party", "HubSpot form analytics", "allude")
        add("Clay — seniority / industry", f"{cl['seniority']} · {cl['industry']}",
            "broker", "Clay enrichment waterfall", "allude")
        if cl.get("income_band"):
            add("Clay — modeled income", cl["income_band"], "broker", "Clay enrichment waterfall", "hold")
    elif ident and ident["kind"] == "resolved":
        for c in ident["resolved"].get("captured", []):
            add(c["label"], c["value"], "declared", "work-email domain → PDL", c["policy"])
    return rows


def sample_login_email() -> str:
    """The cohort email published on the showcase card (synthetic)."""
    return "maya.chen@gauntletai.com"


def sample_magic_token() -> str:
    """The magic token embedded in the sample email entry link (synthetic recipient)."""
    return CO.magic_token(CO.BY_ID["liam"])
