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
from pipeline.personalization import image_gen as IG
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
# X.com ad variants — 12 total = one per real X Ads Manager targeting type.
#
# Categories on /ad-lp:
#   demographic — Location, Language, Device/platform/Wi-Fi, Age, Gender
#   audience    — Conversation, Event, Post Engager, Keyword, Movies & TV,
#                 Interest, Follower look-alikes
#
# Each variant carries utm_campaign=x-{type-slug} and utm_content=v01–v12.
# Copy follows docs/research/copy-personalization-research.md: 60–90 words, one idea,
# soft CTA, loss framing where signal-derived, matched-peer social proof, one trigger.
# Age/gender may target in X Ads but the landing page holds those facts — never recited.
# --------------------------------------------------------------------------- #
AD_CATEGORIES = (
    {"key": "demographic", "label": "Demographic & delivery"},
    {"key": "audience", "label": "Audience & intent"},
)

AUDIENCE_FIT = {
    "CTO": {"label": "CTO / VP Engineering", "avatar": "CT", "accent": "#3b82f6"},
    "Engineer": {"label": "Senior Engineer", "avatar": "SE", "accent": "#10b981"},
    "HR/L&D": {"label": "HR / L&D Leader", "avatar": "LD", "accent": "#a855f7"},
    "cross-audience": {"label": "Cross-audience", "avatar": "GA", "accent": "#64748b"},
}

_AUDIENCE_ROUTE = {"CTO": "companies", "Engineer": "individuals",
                   "HR/L&D": "companies", "cross-audience": "neutral"}


def _v(id_, variant_id, category, audience_fit, x_targeting_type, x_targeting_example,
       utm_campaign, *,
       trigger, body, proof, cta_label,
       h1_pre, h1_gold, sub, hero_eyebrow="",
       cta_primary, cta_secondary,
       compare_emphasis, order=None,
       prove_intro=None, challenger_body=None, challenger_hot=False,
       cta_heading=None, cta_sub=None, stat_highlight=None,
       hold_note=None):
    """Build one ad variant dict with paired ad mockup + landing-page overrides."""
    fit = AUDIENCE_FIT[audience_fit]
    return {
        "id": id_,
        "variant_id": variant_id,
        "category": category,
        "audience_fit": audience_fit,
        "audience_fit_label": fit["label"],
        "x_targeting_type": x_targeting_type,
        "x_targeting_example": x_targeting_example,
        "audience": _AUDIENCE_ROUTE[audience_fit],
        "utm_campaign": utm_campaign,
        "utm_source": "x",
        "utm_medium": "paid",
        "hold_note": hold_note,
        "ad": {
            "handle": "GauntletAI",
            "display": "Gauntlet AI",
            "avatar": fit["avatar"],
            "accent": fit["accent"],
            "trigger": trigger,
            "body": body,
            "proof": proof,
            "cta_label": cta_label,
            "text": f"{trigger} {body} {proof}",
        },
        "page": {
            "hero_eyebrow": hero_eyebrow or f"From your X ad · {x_targeting_type}",
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
    # --- Demographic & delivery (v01–v05) ---
    _v("x-location", "v01", "demographic", "CTO",
       "Location targeting", "SF Bay Area · Austin · Seattle metro",
       "x-location-tech-hubs",
       trigger="Bay Area and Austin CTOs tell us the same hiring story.",
       body=("Three ML roles open for months while AI pilots sit idle — the bottleneck isn't "
             "models, it's engineers who've already shipped under production pressure."),
       proof=("Owner and Mainsail Partners hire from Gauntlet cohorts where 5,000+ applicants "
              "compete and capability is observed across ten weeks, not a whiteboard loop."),
       cta_label="See how they prove it →",
       hero_eyebrow="You clicked the location-targeted ad",
       h1_pre="Tech Hubs Don't Have an AI Model Problem. ",
       h1_gold="They Have a Talent Proof Problem.",
       sub=("SF, Austin, Seattle — same pattern: pilots work, hiring stalls on skills you can't "
            "observe in 45 minutes. Gauntlet places engineers whose capability has already been "
            "proven across ten weeks of production pressure."),
       cta_primary="Hire Proven Talent", cta_secondary="See the Proof Model",
       compare_emphasis="gauntlet",
       prove_intro=("Regional tech leaders hire from Gauntlet cohorts where execution is observed "
                    "across weeks — not compressed into interview theater."),
       cta_heading="Your next AI hire shouldn't be a guess",
       cta_sub="Watch engineers prove it before you sign the offer.",
       stat_highlight=0),
    _v("x-language", "v02", "demographic", "cross-audience",
       "Language targeting", "English (United States)",
       "x-language-en-us",
       trigger="Most AI pilots stall — and it's rarely the model.",
       body=("The pattern we hear from engineering leaders: the technology works, but nobody on "
             "the team can operate it under production load."),
       proof=("Gauntlet transforms engineers into AI-first operators — hire proven talent or "
              "upskill your existing team with Catalyst. 20,000+ applicants to date."),
       cta_label="Worth a look? →",
       hero_eyebrow="You clicked the language-targeted ad",
       h1_pre="The Direct Path for US Engineering Teams to Go ", h1_gold="AI-First",
       sub=("No jargon, no translation layer — Gauntlet transforms engineers into AI-first operators "
            "because most AI pilots don't have a technology problem, they have a talent problem. "
            "Hire proven engineers or upskill the team you already have."),
       cta_primary="Hire Proven Talent", cta_secondary="Upskill Your Team",
       compare_emphasis="catalyst",
       prove_intro=("We can train your existing team to build AI-native or place engineers who've "
                    "already proven it, week after week, under real production pressure."),
       cta_heading="Go all-in on AI",
       cta_sub="Most AI pilots stall. Gauntlet engineers ship.",
       stat_highlight=2),
    _v("x-device", "v03", "demographic", "CTO",
       "Device, platform, & Wi-Fi targeting", "Desktop · Wi-Fi connected · Office hours",
       "x-device-wifi-office",
       trigger="B2B buyers research AI hiring solutions at their desk — not on the couch.",
       body=("When you're evaluating talent programs during work hours, you need proof models "
             "that survive scrutiny, not marketing decks."),
       proof=("Gauntlet's Hire track places engineers observed across 80-hour weeks. Catalyst "
              "rewires existing teams in six weeks. Both tied to production outcomes."),
       cta_label="Open to the breakdown? →",
       hero_eyebrow="You clicked the device-targeted ad",
       h1_pre="Evaluate AI Talent Programs ", h1_gold="Like You Evaluate Vendors",
       sub=("Desktop research deserves desktop proof — cohort demos, comparison tables, and "
            "engineers who've shipped 10+ production apps under sustained pressure. No slide decks."),
       cta_primary="Compare Hire vs Catalyst", cta_secondary="See the Proof Model",
       compare_emphasis="catalyst",
       order=["hero", "compare", "prove", "numbers", "challenger", "cta"],
       prove_intro=("Side-by-side comparison: 10-week Hire track for net-new capability, "
                    "6-week Catalyst for the team you already have. Same proof philosophy."),
       cta_heading="Proof that survives due diligence",
       cta_sub="Watch engineers ship before you commit budget.",
       stat_highlight=1),
    _v("x-age", "v04", "demographic", "Engineer",
       "Age targeting", "28–45",
       "x-age-senior-engineer",
       trigger="Senior engineers who made the AI leap tell us the same thing.",
       body=("The difference wasn't another cert — it was ten weeks of sustained observation "
             "under real production pressure."),
       proof=("One Challenger shipped 12 production systems in training. Traditional interviews "
              "would have missed every signal that mattered."),
       cta_label="Worth applying? →",
       hero_eyebrow="You clicked the senior-engineer ad",
       h1_pre="The Career Leap Experienced Engineers ", h1_gold="Regret Waiting On",
       sub=("Gauntlet Challenger is a 10-week immersive cohort where you build RAG pipelines, agents, "
            "and workflows — then demo them live under scrutiny. Prove the leap, don't pitch it."),
       cta_primary="Apply to Challenger →", cta_secondary="See Alumni Outcomes",
       compare_emphasis="gauntlet",
       order=["hero", "challenger", "prove", "compare", "numbers", "cta"],
       challenger_hot=True,
       challenger_body=("Apply to train as a Gauntlet Challenger — 10 weeks, full-time, everything covered. "
                        "5,000+ applicants per cohort. Standards rise every week."),
       prove_intro=("You've shipped before — this is how we prove you can ship AI-native. Weekly live "
                    "reviews, escalating complexity, sustained observation across ten weeks."),
       cta_heading="Stop waiting for permission to go AI-first",
       cta_sub="Ten weeks. Full-time. Everything covered. Prove it under pressure.",
       stat_highlight=1,
       hold_note="Age targets in X Ads (28–45) but landing page holds age — never recited (surface policy)"),
    _v("x-gender", "v05", "demographic", "cross-audience",
       "Gender targeting", "All genders (broad reach)",
       "x-gender-all",
       trigger="5,000+ engineers apply per Gauntlet cohort — selection is on execution, not demographics.",
       body=("The Challenger program observes how you ship under production pressure across ten weeks. "
             "Every week requires deployed code and working systems."),
       proof=("Challengers who complete the program ship 10+ production apps. The credential means "
              "something because the bar is real."),
       cta_label="See how selection works →",
       hero_eyebrow="You clicked the Gauntlet ad",
       h1_pre="Prove You're an ", h1_gold="AI-First Engineer",
       sub=("Gauntlet Challenger is a 10-week immersive cohort where capability is observed under "
            "real production pressure — shipped code, deployed systems, live demos. The evaluation "
            "is the program."),
       cta_primary="Become a Challenger →", cta_secondary="Hire Proven Talent",
       compare_emphasis="gauntlet",
       challenger_hot=True,
       prove_intro=("Production only. Weekly live reviews. Escalating complexity. "
                    "By the end you've shown how you adapt — not just what you can do on a good day."),
       cta_heading="Think this is you?",
       cta_sub="Most engineers wait. Challengers ship.",
       stat_highlight=0,
       hold_note="Gender may target in X Ads but landing page holds gender — never recited (surface policy)"),
    # --- Audience & intent (v06–v12) ---
    _v("x-conversation", "v06", "audience", "CTO",
       "Conversation targeting", "Threads about \"AI transformation\" · \"engineering velocity\"",
       "x-conversation-ai-transform",
       trigger="Your Q3 note mentioned doubling the engineering org.",
       body=("When teams scale that fast, the bottleneck isn't models — it's engineers who can "
             "operate AI-first under production load."),
       proof=("Catalyst rewired Northwind's existing team in six weeks — engineers came back building "
              "RAG pipelines and agent workflows, not slide decks."),
       cta_label="Worth a look? →",
       hero_eyebrow="You clicked the conversation-targeted ad",
       h1_pre="Your Engineers Ship Features. ", h1_gold="Catalyst Teaches Them to Ship AI.",
       sub=("A 6-week immersive cohort for the team you already have — real AI systems: RAG pipelines, "
            "agents, workflows, MCP. Because most AI pilots don't have a technology problem, they have a talent problem."),
       cta_primary="Upskill Your Team", cta_secondary="Hire Instead",
       compare_emphasis="catalyst",
       prove_intro=("We train your existing engineers to build AI-native — week after week, under real "
                    "production pressure. Catalyst is the fastest path when hiring isn't the bottleneck."),
       cta_heading="Rewire the team you already have",
       cta_sub="Six weeks. Full-time step-out. Engineers who come back as internal AI champions.",
       stat_highlight=1),
    _v("x-event", "v07", "audience", "HR/L&D",
       "Event targeting", "HR Tech Conference · DevOps Days attendees",
       "x-event-hrtech",
       trigger="Your L&D budget buys courses. Catalyst buys engineers who come back different.",
       body=("Six weeks, full-time step-out — your engineers build real RAG pipelines and agent "
             "workflows, not slide decks."),
       proof=("HR leaders at 200–500 person tech shops say upskilling wins when engineers ship "
              "production AI systems tied to business ROI."),
       cta_label="Worth sending the overview? →",
       hero_eyebrow="You clicked the event-targeted ad",
       h1_pre="Your L&D Budget Buys Courses. ", h1_gold="Catalyst Buys AI Champions.",
       sub=("A 6-week immersive cohort for engineers you select — real AI systems, production-grade "
            "capstone tied to business ROI. They come back as internal AI leads, not certificate holders."),
       cta_primary="Upskill Your Team", cta_secondary="See Catalyst Details",
       compare_emphasis="catalyst",
       prove_intro=("Catalyst rewires the team you already have — engineers step out full-time for six weeks "
                    "and return building AI-native systems your org can actually deploy."),
       cta_heading="Turn your L&D line item into AI capability",
       cta_sub="Per-employee fee. Engineers you select. Champions you keep.",
       stat_highlight=1),
    _v("x-engager", "v08", "audience", "cross-audience",
       "Post Engager targeting", "Engaged with @GauntletAI posts (last 30 days)",
       "x-engager-retarget",
       trigger="You liked our post about the Challenger selection rate — here's the full picture.",
       body=("5,000+ engineers apply per cohort. Ten weeks, full-time, everything covered — "
             "capability observed under 80-hour weeks, not interview composure."),
       proof=("Challengers who complete the program ship 10+ production apps. Companies hire from "
              "the same proof model on the Hire track."),
       cta_label="Pick up where you left off →",
       hero_eyebrow="Welcome back from X",
       h1_pre="You Saw the Selection Rate. ", h1_gold="Here's the Proof Model.",
       sub=("Whether you're hiring AI-native engineers or applying to Challenger yourself — "
            "Gauntlet observes execution across weeks of production pressure. Same philosophy, "
            "two delivery tracks."),
       cta_primary="Hire Proven Talent", cta_secondary="Become a Challenger →",
       compare_emphasis="gauntlet",
       order=["hero", "prove", "compare", "challenger", "numbers", "cta"],
       prove_intro=("You already know the bar is high — here's how we prove capability: sustained "
                    "observation, weekly live reviews, escalating complexity across ten weeks."),
       cta_heading="Ready for the next step?",
       cta_sub="Hire proven engineers or prove you're one.",
       stat_highlight=0),
    _v("x-keyword", "v09", "audience", "CTO",
       "Keyword targeting", "\"AI engineer hiring\" · \"ML team build\" · \"AI talent gap\"",
       "x-keyword-ai-hiring",
       trigger="Saw your team posted three ML engineer roles last month.",
       body=("Usually means you're hiring for skills you can only observe in a 45-minute loop — "
             "while AI pilots sit idle."),
       proof=("Most Series B CTOs tell us the last three AI hires took six months to ramp. "
              "Gauntlet places engineers who've shipped 10+ production apps under 80-hour weeks."),
       cta_label="See how they prove it →",
       hero_eyebrow="You clicked the keyword-targeted ad",
       h1_pre="Stop Interviewing for Skills You ", h1_gold="Can't Observe in 45 Minutes",
       sub=("Gauntlet places engineers whose capability has already been observed across ten weeks "
            "of production pressure — not a whiteboard loop. 5,000+ applicants per cohort; you watch them ship."),
       cta_primary="Hire Proven Talent", cta_secondary="See the Proof Model",
       compare_emphasis="gauntlet",
       prove_intro=("Traditional interviews compress signal into hours. Gauntlet observes execution "
                    "across weeks — the hire track shows you engineers who've already shipped under pressure."),
       cta_heading="Your next AI hire shouldn't be a guess",
       cta_sub="Watch engineers prove it before you sign the offer.",
       stat_highlight=0),
    _v("x-movies", "v10", "audience", "Engineer",
       "Movies & TV targeting", "Tech documentaries · startup culture · AI deep-dives",
       "x-movies-tech-docs",
       trigger="If you've watched every AI documentary and still haven't shipped one yourself —",
       body=("The gap between watching and building is ten weeks of sustained production pressure. "
             "That's what Challenger is for."),
       proof=("Challengers ship 10+ production apps during training — RAG pipelines, agents, workflows. "
              "Weekly live reviews under scrutiny, not tutorial follow-alongs."),
       cta_label="Worth applying? →",
       hero_eyebrow="You clicked the documentary-viewer ad",
       h1_pre="Stop Watching AI Stories. ", h1_gold="Start Shipping AI Systems.",
       sub=("Gauntlet Challenger is a 10-week immersive cohort where you build and deploy real AI systems — "
            "not watch others do it. Every week requires shipped code and working demos."),
       cta_primary="Become a Challenger →", cta_secondary="See How We Prove It",
       compare_emphasis="gauntlet",
       challenger_hot=True,
       challenger_body=("Apply to train as a Gauntlet Challenger — 10 weeks, full-time, everything covered. "
                        "Build the systems you've been reading about."),
       prove_intro=("Production only. Weekly live reviews. By the end you've shipped what most engineers "
                    "only talk about — agents, RAG, MCP integrations."),
       cta_heading="Your turn to be in the documentary",
       cta_sub="Ten weeks. Full-time. Everything covered.",
       stat_highlight=0),
    _v("x-interest", "v11", "audience", "Engineer",
       "Interest targeting", "Enterprise software · AI/ML · Developer tools",
       "x-interest-ai-ml",
       trigger="5,000+ engineers apply per Gauntlet cohort.",
       body=("Ten weeks, full-time, everything covered — you prove you can ship AI systems under "
             "80-hour weeks, not interview composure."),
       proof=("Challengers who complete the program ship 10+ production apps. The selection rate "
              "makes the credential mean something."),
       cta_label="Worth applying? →",
       hero_eyebrow="You clicked the interest-targeted ad",
       h1_pre="10 Weeks to Prove You're an ", h1_gold="AI-First Engineer",
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
    _v("x-lookalike", "v12", "audience", "CTO",
       "Follower look-alikes targeting", "Lookalikes of @karpathy · @sama · @elaborateeng",
       "x-lookalike-eng-leaders",
       trigger="CTOs who follow Karpathy and Sama usually care about one thing: talent density.",
       body=("You can't hire your way to AI-first with whiteboard loops — you need engineers "
             "whose capability has been observed under production pressure."),
       proof=("Gauntlet cohorts produce engineers who ship 10+ production apps in ten weeks. "
              "Owner and Mainsail Partners hire from the same proof model."),
       cta_label="See the hire track →",
       hero_eyebrow="You clicked the lookalike-targeted ad",
       h1_pre="Talent Density Beats ", h1_gold="Talent Volume",
       sub=("Engineering leaders who follow the best builders know: capability is observed, not "
            "interviewed. Gauntlet places engineers proven across ten weeks of 80-hour production weeks."),
       cta_primary="Hire Proven Talent", cta_secondary="See the Proof Model",
       compare_emphasis="gauntlet",
       prove_intro=("The engineers you admire built under pressure — Gauntlet observes the same signal "
                    "across ten weeks before you ever sign an offer."),
       cta_heading="Hire like the leaders you follow",
       cta_sub="Watch engineers prove it before you commit.",
       stat_highlight=2),
]

AD_BY_CAMPAIGN = {v["utm_campaign"]: v for v in AD_VARIANTS}
AD_BY_VARIANT_ID = {v["variant_id"]: v for v in AD_VARIANTS}


def resolve_ad_variant(entry: dict) -> dict | None:
    """Map UTM campaign + content to one of the 12 catalogued X.com ad variants."""
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


def ad_grid_sections() -> list[dict]:
    """Grouped grid data for /ad-lp: two X Ads Manager categories × 6 variants each."""
    by_cat: dict[str, list[dict]] = {c["key"]: [] for c in AD_CATEGORIES}
    for v in AD_VARIANTS:
        by_cat[v["category"]].append(v)
    return [{"category": c["key"], "label": c["label"], "variants": by_cat[c["key"]]}
            for c in AD_CATEGORIES]


def ad_grid_rows() -> list[dict]:
    """Backward-compatible alias — returns category sections."""
    return ad_grid_sections()


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
# Objection catalog — sales psychology, truth-bounded (Gauntlet site claims only)
# Each objection: id, text, tracks[], weight_signals[], reframe slots, optional blocked_say.
# --------------------------------------------------------------------------- #
TRACKS = ("hire", "catalyst", "challenger")

_AD_SIGNAL = {v["id"]: f"ad_{v['id'].replace('x-', '')}" for v in AD_VARIANTS}

OBJECTION_CATALOG: list[dict] = [
    # --- Hire (Gauntlet) ---
    {"id": "open_market_hire",
     "text": "We can hire AI talent on the open market",
     "tracks": ["hire"],
     "signals": [("ad_keyword", 14), ("ad_lookalike", 10), ("audience_fit_cto", 12),
                 ("audience_route_b2b_hire", 8), ("network_corporate", 6), ("archetype_prestige", 5)],
     "reframe": {
         "hero_sub": ("Open-market listings look fine until six months of ramp on skills a "
                      "45-minute loop never surfaces. Gauntlet places engineers observed across "
                      "ten weeks of production pressure — 5,000+ applicants per cohort."),
         "prove_card": (2, "Traditional interviews compress signal into hours. Our programs "
                        "observe execution across weeks — patterns that matter only become visible over time."),
         "compare_row": "Selection",
     }},
    {"id": "ten_weeks_long",
     "text": "10 weeks is too long to evaluate someone",
     "tracks": ["hire"],
     "signals": [("ad_keyword", 12), ("ad_device", 9), ("audience_fit_cto", 10),
                 ("audience_route_b2b_hire", 7), ("network_corporate", 5)],
     "reframe": {
         "hero_sub": ("Ten weeks sounds long until you compare it to six months of ramp after a "
                      "45-minute hire. Gauntlet compresses evaluation into sustained observation — "
                      "you watch engineers ship 10+ production apps before you sign."),
         "prove_card": (2, "Sustained observation across weeks reveals what a single interview cannot — "
                        "reasoning, decision-making, and response to pressure under real load."),
         "compare_row": "Weekly hours",
     }},
    {"id": "placement_fees",
     "text": "Placement fees are too expensive",
     "tracks": ["hire"],
     "signals": [("archetype_cost_confident", 12), ("preferential_cost", 10), ("ad_device", 7),
                 ("audience_route_b2b_hire", 6), ("network_corporate", 5)],
     "reframe": {
         "hero_sub": ("A bad AI hire costs more than a placement fee — months of idle pilots while "
                      "the team ramps. Gauntlet credits are pre-purchased; you pay after capability "
                      "has been observed across ten weeks."),
         "compare_row": "Pricing",
         "compare_emphasis": "gauntlet",
         "final_cta_sub": "Watch engineers prove it before you commit budget.",
     },
     "blocked_say": "We priced this for your modeled income band — here's the plan we'd push"},
    {"id": "internal_upskill",
     "text": "Our team can upskill internally instead",
     "tracks": ["hire", "catalyst"],
     "signals": [("ad_conversation", 11), ("ad_language", 8), ("audience_route_b2b_hire", 7),
                 ("audience_companies", 6), ("archetype_prestige", 5)],
     "reframe": {
         "hero_sub": ("Internal upskilling works when engineers can step out full-time — most teams "
                      "can't. Catalyst rewires the team you already have in six weeks; Hire places "
                      "engineers who've already proven it."),
         "compare_emphasis": "catalyst",
         "prove_card": (0, "Every week requires shipped code and working systems — the same bar "
                        "whether you hire net-new or rewire existing engineers."),
     }},
    {"id": "wrong_stack",
     "text": "We don't know if they can ship in OUR stack",
     "tracks": ["hire"],
     "signals": [("tier_2", 8), ("tier_3", 10), ("industry_resolved", 9), ("audience_fit_cto", 7),
                 ("network_corporate", 6)],
     "reframe": {
         "hero_sub": ("Stack fit isn't a whiteboard question — it's a production question. Challengers "
                      "ship 10+ apps across web, mobile, and AI systems under 80-hour weeks; you observe "
                      "how they adapt before you commit."),
         "prove_card": (3, "Standards rise every week. By the end you've seen how engineers adapt — "
                        "not just what they can do on a good day."),
         "compare_row": "What they build",
     }},
    {"id": "bootcamp_burned",
     "text": "We've been burned by bootcamp hires before",
     "tracks": ["hire"],
     "signals": [("ad_location", 8), ("ad_lookalike", 9), ("audience_fit_cto", 8),
                 ("audience_route_b2b_hire", 6), ("network_corporate", 5)],
     "reframe": {
         "hero_sub": ("Bootcamps certify attendance — Gauntlet observes execution. 5,000+ applicants "
                      "per cohort; capability is proven across ten weeks of production pressure, not "
                      "a capstone weekend."),
         "prove_card": (0, "This isn't preparation for evaluation. It is the evaluation — shipped code "
                        "and working systems every week."),
         "compare_row": "Validation",
     }},
    # --- Catalyst (upskill) ---
    {"id": "no_time_away",
     "text": "My engineers don't have time to step away",
     "tracks": ["catalyst"],
     "signals": [("ad_conversation", 12), ("ad_device", 9), ("audience_fit_cto", 8),
                 ("audience_route_b2b_upskill", 10), ("audience_companies", 6)],
     "reframe": {
         "hero_sub": ("Six weeks full-time step-out sounds like a lot — until another quarter passes "
                      "with pilots idle. Catalyst is built for engineers you select; they return as "
                      "internal AI champions, not certificate holders."),
         "compare_row": "Weekly hours",
         "compare_emphasis": "catalyst",
     }},
    {"id": "ld_budget_committed",
     "text": "L&D budget is already committed",
     "tracks": ["catalyst"],
     "signals": [("ad_event", 14), ("audience_fit_hr", 12), ("audience_route_b2b_upskill", 10),
                 ("archetype_prestige", 4)],
     "reframe": {
         "hero_sub": ("Most L&D line items buy courses — Catalyst buys engineers who come back building "
                      "RAG pipelines and agent workflows. Per-employee fee; production-grade capstone "
                      "tied to business ROI."),
         "compare_row": "Pricing",
         "compare_emphasis": "catalyst",
         "final_cta_sub": "Per-employee fee. Engineers you select. Champions you keep.",
     }},
    {"id": "six_weeks_revert",
     "text": "6 weeks won't stick — they'll revert",
     "tracks": ["catalyst"],
     "signals": [("ad_event", 10), ("ad_conversation", 9), ("audience_fit_hr", 8),
                 ("audience_route_b2b_upskill", 7)],
     "reframe": {
         "hero_sub": ("Short courses fade because nothing ships. Catalyst engineers build real AI systems "
                      "— RAG pipelines, agents, workflows, MCP — with a production-grade capstone tied to "
                      "your business ROI."),
         "prove_card": (0, "Every week requires shipped code and working systems — engineers demo deployed "
                        "systems under scrutiny, not slide decks."),
         "compare_row": "Capstone",
     }},
    {"id": "roi_unproven",
     "text": "ROI is unproven for our org",
     "tracks": ["catalyst"],
     "signals": [("ad_event", 9), ("audience_fit_hr", 10), ("audience_route_b2b_upskill", 8),
                 ("archetype_outcomes_first", 6), ("network_corporate", 5)],
     "reframe": {
         "hero_sub": ("ROI shows up when engineers ship production AI systems tied to business outcomes — "
                      "not when they collect certificates. Catalyst capstones are production-grade and "
                      "tied to business ROI."),
         "prove_card": (1, "Weekly live reviews let you observe reasoning and decision-making under "
                        "pressure — the signals that predict whether capability sticks."),
         "compare_row": "Capstone",
     }},
    {"id": "need_hires_not_training",
     "text": "We need hires, not training",
     "tracks": ["catalyst", "hire"],
     "signals": [("ad_keyword", 11), ("ad_location", 8), ("audience_route_b2b_hire", 9),
                 ("audience_companies", 7), ("seniority_exec", 6)],
     "reframe": {
         "hero_sub": ("When hiring is the bottleneck, the Hire track places engineers who've already "
                      "shipped 10+ production apps across ten weeks. Same proof philosophy — "
                      "different delivery."),
         "compare_emphasis": "gauntlet",
         "compare_row": "Best for",
     }},
    # --- Challenger (individual) ---
    {"id": "cant_take_10_weeks",
     "text": "I can't take 10 weeks off work",
     "tracks": ["challenger"],
     "signals": [("ad_age", 10), ("ad_movies", 8), ("audience_fit_engineer", 9),
                 ("audience_route_individual", 8), ("network_residential", 5)],
     "reframe": {
         "hero_sub": ("Ten weeks full-time is a real trade — everything covered, but not part-time. "
                      "Challengers who complete the program ship 10+ production apps; the credential "
                      "means something because the bar is real."),
         "challenger_body": ("Apply to train as a Gauntlet Challenger — 10 weeks, full-time, everything "
                             "covered. Next cohort starts September 14."),
         "compare_row": "Next cohort",
     }},
    {"id": "selection_rate_low",
     "text": "Selection rate is too low — why try?",
     "tracks": ["challenger"],
     "signals": [("hubspot_abandoned", 14), ("ad_engager", 12), ("ad_interest", 10),
                 ("ad_gender", 8), ("audience_route_individual", 7), ("intent_hot", 6)],
     "reframe": {
         "hero_sub": ("5,000+ engineers apply per cohort — the bar is high because the credential has "
                      "to mean something. Selection is on execution under 80-hour weeks, not interview "
                      "composure."),
         "challenger_body": ("5,000+ applicants per cohort. Standards rise every week. If you've already "
                             "started an application, pick up where you left off."),
         "prove_card": (0, "This isn't preparation for evaluation. It is the evaluation — every week "
                        "requires shipped code and working systems."),
         "final_cta_sub": "Most engineers wait. Challengers ship.",
     },
     "blocked_say": "You abandoned step 3 of 4 — the selection rate scared you off; go back now"},
    {"id": "already_senior",
     "text": "I'm already senior — I don't need training",
     "tracks": ["challenger"],
     "signals": [("ad_age", 14), ("seniority_ic", 10), ("technical", 9), ("lifestage_upskiller", 7),
                 ("audience_fit_engineer", 8), ("audience_route_individual", 6)],
     "reframe": {
         "hero_sub": ("Senior engineers who made the AI leap tell us the gap wasn't another cert — "
                      "it was ten weeks of sustained observation under production pressure. "
                      "Prove the leap; don't pitch it."),
         "challenger_body": ("You've shipped before — Challenger is how you prove you can ship "
                             "AI-native: RAG pipelines, agents, workflows, MCP."),
         "prove_card": (3, "Standards rise every week — by the end you've shown how you adapt under "
                        "escalating complexity, not just what you can do on a good day."),
     }},
    {"id": "learn_on_job",
     "text": "I learn better on the job",
     "tracks": ["challenger"],
     "signals": [("ad_movies", 10), ("ad_interest", 8), ("audience_route_individual", 7),
                 ("network_residential", 5), ("explorer_archetype", 6)],
     "reframe": {
         "hero_sub": ("On-the-job learning works until production pressure exposes gaps you can't "
                      "see in tickets. Challenger is production only — weekly live reviews under "
                      "scrutiny, 80-hour weeks, shipped systems every week."),
         "prove_card": (1, "Engineers demo deployed systems under scrutiny — you observe reasoning "
                        "and response to pressure, not tutorial follow-alongs."),
     }},
    {"id": "opportunity_cost",
     "text": "The opportunity cost is too high",
     "tracks": ["challenger"],
     "signals": [("archetype_cost_confident", 12), ("preferential_cost", 10), ("ad_age", 8),
                 ("audience_route_individual", 7), ("seniority_ic", 5)],
     "reframe": {
         "hero_sub": ("Ten weeks is expensive — so is another year watching AI pilots from the "
                      "sidelines. Challenger is full-time, everything covered; 20,000+ applicants "
                      "to date compete because the payoff is observed capability, not a certificate."),
         "challenger_body": ("Apply to train as a Gauntlet Challenger — 10 weeks, full-time, "
                             "everything covered. See payment and scholarship options on admissions."),
         "final_cta_sub": "Ten weeks. Full-time. Everything covered. Prove it under pressure.",
     },
     "blocked_say": "We modeled your income band and pre-selected a payment plan — apply now"},
]

OBJECTION_BY_ID = {o["id"]: o for o in OBJECTION_CATALOG}

_SIGNAL_LABELS = {
    "ad_keyword": "X keyword ad (AI hiring intent)",
    "ad_event": "X event ad (HR Tech / DevOps Days)",
    "ad_age": "X age targeting (28–45, held on page)",
    "ad_engager": "X post engager retarget",
    "audience_fit_cto": "Ad audience fit: CTO / VP Engineering",
    "audience_fit_hr": "Ad audience fit: HR / L&D",
    "audience_fit_engineer": "Ad audience fit: Senior Engineer",
    "audience_route_b2b_hire": "Audience route: B2B hire",
    "audience_route_b2b_upskill": "Audience route: B2B upskill",
    "audience_route_individual": "Audience route: individual / Challenger",
    "hubspot_abandoned": "HubSpot abandoned application",
    "archetype_cost_confident": "CRM archetype: cost-confident",
    "preferential_cost": "Segment: cost-conscious",
    "seniority_ic": "Clay/LinkedIn: individual contributor",
    "technical": "Clay/LinkedIn: technical profile",
}


def _audience_route(audience: str, ad_variant: dict | None, ident: dict | None) -> str:
    """Narrow audience into hire / upskill / individual / neutral for objection routing."""
    if ad_variant:
        fit = ad_variant["audience_fit"]
        if fit == "HR/L&D":
            return "b2b_upskill"
        if fit == "CTO":
            return "b2b_hire"
        if fit == "Engineer":
            return "individual"
        emph = ad_variant["page"].get("compare_emphasis")
        if emph == "catalyst":
            return "b2b_upskill"
        if emph == "gauntlet":
            return "b2b_hire"
        return "neutral"
    if ident and ident.get("kind") == "cohort":
        li = ident["view"]["linkedin"]
        goal = (ident["view"]["declared"].get("goal") or "").lower()
        if li.get("seniority") == "exec" or "team" in goal:
            return "b2b_upskill" if "upskill" in goal or "team" in goal else "b2b_hire"
        return "individual"
    if audience == "individuals":
        return "individual"
    if audience == "companies":
        return "b2b_hire"
    return "neutral"


def _collect_objection_signals(entry: dict, ad_variant: dict | None, audience: str,
                               tier: int, ident: dict | None, det: dict,
                               route: str) -> set[str]:
    """Active signal keys for objection scoring — derived from entry, IP, CRM, ad variant."""
    sigs: set[str] = {f"channel_{entry['channel']}"}
    sigs.add(f"audience_{audience}")
    sigs.add(f"audience_route_{route}")
    sigs.add(f"tier_{tier}")
    net = det.get("network_type", "")
    if net in ("corporate", "corporate (via VPN)"):
        sigs.add("network_corporate")
    if net in ("residential", "consumer ISP", "mobile"):
        sigs.add("network_residential")
    if det.get("industry"):
        sigs.add("industry_resolved")
    if ad_variant:
        sigs.add(_AD_SIGNAL[ad_variant["id"]])
        fit = ad_variant["audience_fit"]
        _fit_sig = {"CTO": "audience_fit_cto", "HR/L&D": "audience_fit_hr",
                    "Engineer": "audience_fit_engineer"}.get(fit)
        if _fit_sig:
            sigs.add(_fit_sig)
        if ad_variant["page"].get("compare_emphasis") == "catalyst":
            sigs.add("campaign_catalyst")
        elif ad_variant["page"].get("compare_emphasis") == "gauntlet":
            sigs.add("campaign_hire")
    intent = _campaign_intent(entry.get("utm_campaign"))
    if intent == "companies":
        sigs.add("campaign_companies")
    elif intent == "individuals":
        sigs.add("campaign_individuals")
    if ident and ident.get("kind") == "cohort":
        v, arch = ident["view"], ident["archetype"]
        sigs.add(f"archetype_{arch['id']}")
        if arch["id"] == "explorer":
            sigs.add("explorer_archetype")
        hs, li, dec = v["hubspot"], v["linkedin"], v["declared"]
        if hs.get("abandoned"):
            sigs.add("hubspot_abandoned")
        if hs.get("lead_score", 0) >= 80 or hs.get("lifecycle") == "sql":
            sigs.add("intent_hot")
        if li.get("seniority") == "exec":
            sigs.add("seniority_exec")
        elif li.get("seniority") in ("ic", "career_change"):
            sigs.add("seniority_ic")
        if li.get("technical"):
            sigs.add("technical")
        goal = (dec.get("goal") or "").lower()
        if any(w in goal for w in ("afford", "broke", "cost", "cheap")):
            sigs.add("preferential_cost")
        for fam, d in ident["segments"].items():
            for s in d["segments"]:
                if s["id"] == "cost":
                    sigs.add("preferential_cost")
                if s["id"] == "upskiller":
                    sigs.add("lifestage_upskiller")
    return sigs


def _objection_applies(obj: dict, route: str) -> bool:
    """Objection must match at least one track for the visitor's route."""
    tracks = obj["tracks"]
    if route == "b2b_hire":
        return "hire" in tracks
    if route == "b2b_upskill":
        return "catalyst" in tracks
    if route == "individual":
        return "challenger" in tracks
    return True  # neutral — all tracks eligible


def prioritize_objections(ctx: dict) -> list[dict]:
    """Rank top 3–5 objections for this visitor. ctx: entry, ad_variant, audience, tier, ident, det."""
    route = ctx["route"]
    active = _collect_objection_signals(
        ctx["entry"], ctx.get("ad_variant"), ctx["audience"], ctx["tier"],
        ctx.get("ident"), ctx["det"], route)
    scored: list[dict] = []
    for obj in OBJECTION_CATALOG:
        if not _objection_applies(obj, route):
            continue
        score = 0
        matched: list[str] = []
        for sig, weight in obj["signals"]:
            if sig in active:
                score += weight
                matched.append(sig)
        if score <= 0:
            continue
        why_parts = [_SIGNAL_LABELS.get(m, m.replace("_", " ")) for m in matched[:3]]
        scored.append({
            "objection": obj,
            "objection_id": obj["id"],
            "text": obj["text"],
            "score": score,
            "signal_source": matched,
            "why_prioritized": " + ".join(why_parts) if why_parts else "context match",
            "rank": 0,
        })
    scored.sort(key=lambda x: (-x["score"], x["objection_id"]))
    top = scored[:5]
    for i, row in enumerate(top):
        row["rank"] = i + 1
    return top


def _signal_label(sig: str) -> str:
    return _SIGNAL_LABELS.get(sig, sig.replace("_", " "))


def _apply_objection_reframes(hero: dict, prove: dict, challenger: dict, cta: dict,
                              compare_emphasis: str | None, prove_cards: list,
                              prioritized: list[dict], *, preserve_hero_sub: bool = False) -> tuple[dict, dict, dict, dict,
                                                                 str | None, list, str | None, list[dict]]:
    """Weave prioritized objections into copy slots. Returns updated sections + slot assignments."""
    assignments: list[dict] = []
    row_emphasis: str | None = None
    if not prioritized:
        return hero, prove, challenger, cta, compare_emphasis, prove_cards, row_emphasis, assignments

    def _ack(obj: dict) -> str:
        return f"{obj['text']} — fair question. "

    # #1 → hero sub (skip when a declared goal already owns say-level hero sub)
    o1 = prioritized[0]["objection"]
    rf1 = o1.get("reframe", {})
    if rf1.get("hero_sub") and not preserve_hero_sub:
        hero["sub"] = _ack(o1) + rf1["hero_sub"]
        assignments.append({"rank": 1, "objection_id": o1["id"], "objection": o1["text"],
                            "slot": "hero_sub", "policy": "allude"})

    # #2 → prove card
    if len(prioritized) > 1:
        o2 = prioritized[1]["objection"]
        rf2 = o2.get("reframe", {})
        if rf2.get("prove_card"):
            idx, extra = rf2["prove_card"]
            title, body = prove_cards[idx]
            prove_cards[idx] = (title, body + " " + extra)
            assignments.append({"rank": 2, "objection_id": o2["id"], "objection": o2["text"],
                                "slot": f"prove_card_{idx}", "policy": "allude"})
        if rf2.get("compare_row") and not row_emphasis:
            row_emphasis = rf2["compare_row"]
            assignments.append({"rank": 2, "objection_id": o2["id"], "objection": o2["text"],
                                "slot": "compare_row", "policy": "allude"})
        if rf2.get("compare_emphasis"):
            compare_emphasis = rf2["compare_emphasis"]

    # #3 → prove card or compare / challenger
    if len(prioritized) > 2:
        o3 = prioritized[2]["objection"]
        rf3 = o3.get("reframe", {})
        if rf3.get("challenger_body"):
            challenger["body"] = rf3["challenger_body"]
            assignments.append({"rank": 3, "objection_id": o3["id"], "objection": o3["text"],
                                "slot": "challenger_body", "policy": "allude"})
        elif rf3.get("prove_card"):
            idx, extra = rf3["prove_card"]
            title, body = prove_cards[idx]
            if extra not in body:
                prove_cards[idx] = (title, body + " " + extra)
            assignments.append({"rank": 3, "objection_id": o3["id"], "objection": o3["text"],
                                "slot": f"prove_card_{idx}", "policy": "allude"})
        if rf3.get("compare_row"):
            row_emphasis = rf3["compare_row"]
            assignments.append({"rank": 3, "objection_id": o3["id"], "objection": o3["text"],
                                "slot": "compare_row", "policy": "allude"})
        if rf3.get("compare_emphasis"):
            compare_emphasis = rf3["compare_emphasis"]

    # #1 may also set compare row / emphasis if not consumed
    if rf1.get("compare_row") and not row_emphasis:
        row_emphasis = rf1["compare_row"]
        assignments.append({"rank": 1, "objection_id": o1["id"], "objection": o1["text"],
                            "slot": "compare_row", "policy": "allude"})
    if rf1.get("compare_emphasis"):
        compare_emphasis = rf1["compare_emphasis"]
    if rf1.get("challenger_body"):
        challenger["body"] = rf1["challenger_body"]
        assignments.append({"rank": 1, "objection_id": o1["id"], "objection": o1["text"],
                            "slot": "challenger_body", "policy": "allude"})

    # Final CTA — last prioritized objection with final_cta_sub, else #4/#5
    for row in reversed(prioritized):
        rf = row["objection"].get("reframe", {})
        if rf.get("final_cta_sub"):
            cta["sub"] = rf["final_cta_sub"]
            assignments.append({"rank": row["rank"], "objection_id": row["objection_id"],
                                "objection": row["text"], "slot": "final_cta", "policy": "allude"})
            break

    return hero, prove, challenger, cta, compare_emphasis, prove_cards, row_emphasis, assignments


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
                f"the X.com ad used {variant['x_targeting_type']} targeting "
                f"({variant['x_targeting_example']}) — message-match the hero to that promise")
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
        sigs = [
            f"utm_campaign={ad_variant['utm_campaign']}",
            f"utm_content={ad_variant['variant_id']}",
            f"x_targeting_type={ad_variant['x_targeting_type']}",
            f"x_targeting_example={ad_variant['x_targeting_example']}",
            f"audience_fit={ad_variant['audience_fit']}",
        ]
        why = ("the paid click carried a catalogued X.com campaign — every copy slot "
               "message-matches this variant")
        if ad_variant.get("hold_note"):
            sigs.append(f"hold_policy={ad_variant['hold_note']}")
            why += f" · {ad_variant['hold_note']}"
        t("Ad variant resolve", sigs,
          "AD_BY_CAMPAIGN / AD_BY_VARIANT_ID lookup",
          "observed",
          f"variant = {ad_variant['id']} · {ad_variant['x_targeting_type']}",
          why)

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

    # --- objection-driven reframes (deterministic checklist → copy slots) ---
    prove_cards = [tuple(c) for c in PROVE_CARDS]
    pre_hero_sub = hero["sub"]
    pre_challenger_body = challenger["body"]
    pre_cta_sub = cta["sub"]
    pre_compare_emphasis = compare_emphasis

    aud_route = _audience_route(audience, ad_variant, ident)
    obj_ctx = {"entry": entry, "ad_variant": ad_variant, "audience": audience,
               "tier": tier, "ident": ident, "det": det, "route": aud_route}
    prioritized = prioritize_objections(obj_ctx)
    hero_sub_say = bool(ident and ident["kind"] == "cohort"
                        and ident["view"]["declared"].get("goal"))
    hero, prove, challenger, cta, compare_emphasis, prove_cards, compare_row_emphasis, obj_assignments = \
        _apply_objection_reframes(hero, prove, challenger, cta, compare_emphasis, prove_cards, prioritized,
                                  preserve_hero_sub=hero_sub_say)

    obj_blocked = [{"objection_id": row["objection"]["id"], "text": row["objection"]["text"],
                    "blocked_say": row["objection"].get("blocked_say")}
                   for row in prioritized if row["objection"].get("blocked_say")]

    if hero["sub"] != pre_hero_sub:
        for d in diff:
            if d["slot"] == "hero_sub":
                d["shipped"] = h1_pre + h1_gold + " · " + hero["sub"]
                d["changed"] = d["generic"] != d["shipped"]
                d["source"] = d["source"] + " + objection #" + str(prioritized[0]["rank"])
                d["why"] = (d.get("why", "") + " · objection #" + str(prioritized[0]["rank"])
                            + " reframe woven into hero sub")
                break
    if challenger["body"] != pre_challenger_body:
        for d in diff:
            if d["slot"] == "challenger_body":
                d["shipped"] = challenger["body"]
                d["changed"] = True
                d["source"] = "objection-driven reframe"
                break
        else:
            slot("challenger_body", "Challenger callout", GENERIC["challenger"]["body"],
                 challenger["body"], "objection-driven reframe", "allude",
                 why="prioritized individual-track objection addressed in callout")
    if cta["sub"] != pre_cta_sub:
        for d in diff:
            if d["slot"] == "final_cta":
                d["shipped"] = cta["heading"] + " · " + cta["sub"]
                d["changed"] = True
                break
    if compare_emphasis != pre_compare_emphasis:
        for d in diff:
            if d["slot"] == "compare_emphasis":
                d["shipped"] = compare_emphasis or "none (equal columns)"
                d["changed"] = True
                d["source"] = "objection-driven reframe"
                break

    obj_trace_sigs = [f"route={aud_route}"] + [f"active={s}" for s in sorted(
        _collect_objection_signals(entry, ad_variant, audience, tier, ident, det, aud_route))[:8]]
    if prioritized:
        obj_trace_sigs.append("ranked=" + " > ".join(
            f"#{r['rank']} {r['objection_id']}({r['score']})" for r in prioritized))
        obj_trace_sigs.append("slots=" + ", ".join(
            f"{a['slot']}←#{a['rank']}" for a in obj_assignments) or "—")
    t("Objection prioritize", obj_trace_sigs,
      "score OBJECTION_CATALOG signals → rank top 3–5 → weave into hero/prove/compare/challenger/CTA",
      "allude",
      f"{len(prioritized)} objections ranked" if prioritized else "no objections matched",
      "sales psychology meets them where they are — every reframe uses only Gauntlet site claims; "
      "blocked say-level variants appear on /dev for contrast")

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

    hero_image = IG.resolve_hero_image({
        "entry": entry, "det": det, "identity": ident, "ad_variant": ad_variant,
        "audience": audience, "audience_route": aud_route, "tier": tier,
        "objections": {"prioritized": prioritized},
        "sections": {"hero": hero, "compare": {"emphasis": compare_emphasis}},
    }, generate=False)
    img_receipt = hero_image.get("receipt") or {}
    img_sigs, img_out, img_why = IG.hero_image_trace(img_receipt)
    t("Hero image resolve", img_sigs,
      "disk cache → (async API if keyed) → scene.image_for gallery → CSS gradient",
      "say", img_out, img_why)

    ledger = _ledger(entry, det, ident)
    ledger.extend(IG.hero_image_ledger_rows(img_receipt))
    login_state = bool(ident and ident.get("via") == "login")
    return {
        "entry": entry, "det": det, "ip_forced": ip_forced, "identity": ident,
        "audience": audience, "audience_rule": aud_rule,
        "tier": tier, "tier_label": tier_label, "confidence": conf,
        "sections": {"hero": hero, "prove": {**prove, "cards": prove_cards},
                     "challenger": challenger,
                     "compare": {"rows": COMPARE_ROWS, "emphasis": compare_emphasis,
                                 "row_emphasis": compare_row_emphasis},
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
        "audience_route": aud_route,
        "objections": {"prioritized": prioritized, "assignments": obj_assignments,
                       "blocked": obj_blocked},
        "trace": trace, "copy_diff": diff, "ledger": ledger,
        "hero_image": hero_image,
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


# --------------------------------------------------------------------------- #
# Process map for /dev — the pipeline as a diagram: every decision, every branch,
# every piece of data each stage reads. Pure function of the built page dict, so
# the diagram can never drift from what actually ran.
# --------------------------------------------------------------------------- #
NETWORK_BRANCHES = ["corporate", "corporate (via VPN)", "consumer ISP", "residential",
                    "mobile", "VPN / proxy", "hosting / cloud", "private / unreachable"]
ROUTE_LABELS = {"b2b_hire": "b2b hire", "b2b_upskill": "b2b upskill",
                "individual": "individual", "neutral": "neutral"}


def _branches(options: list[str], taken: str | None) -> list[dict]:
    return [{"label": o, "taken": o == taken} for o in options]


def process_map(page: dict) -> dict:
    """The /dev process diagram: {inputs, stages}. Each stage carries the data it reads,
    the rule, EVERY branch it could take (the taken one flagged), the output, and an
    anchor into the detail panel below. Skipped stages stay visible, marked skipped —
    the full decision space is always on screen."""
    P = page
    entry, det, ident, ad = P["entry"], P["det"], P["identity"], P.get("ad_variant")
    sig = {s["label"]: s["value"] for s in entry["signals"]}

    # -- data in: everything the pipeline can read, before any decision -------
    inputs = [
        {"label": "Query string",
         "value": ", ".join(f"{s['label']}={s['value']}" for s in entry["signals"]
                            if s["value"] != "—" and s["label"] != "Referer header") or "(empty)",
         "feeds": "entry classify · ad variant · IP override"},
        {"label": "Referer header",
         "value": entry["referer"] or "(none)",
         "feeds": "entry classify (search detection)"},
        {"label": "Client IP + headers",
         "value": (det.get("ip") or "private / unreachable")
                  + (" · ?ip= override" if P.get("ip_forced") else ""),
         "feeds": "IP resolve · tier route"},
        {"label": "Login cookie / magic token",
         "value": (ident["email"] + f" (via {ident['via']})") if ident else "(none — anonymous)",
         "feeds": "identity · CRM · segments"},
    ]

    stages: list[dict] = []

    def stage(id_, title, link, reads, rule, branches, output, why,
              skipped=False, skip_reason=""):
        stages.append({"id": id_, "title": title, "link": link, "reads": reads,
                       "rule": rule, "branches": branches, "output": output, "why": why,
                       "skipped": skipped, "skip_reason": skip_reason})

    # 1 · entry channel
    stage("entry", "Entry classify", "#sec-entry",
          [f"utm_medium={sig.get('utm_medium', '—')}", f"utm_campaign={sig.get('utm_campaign', '—')}",
           f"ref={sig.get('ref', '—')}", f"Referer={'search engine' if entry['channel'] == 'search' and not entry['ref'] else (entry['referer'] and 'set') or '—'}",
           f"e token={'present' if entry['token'] else '—'}"],
          entry["rule"],
          _branches(["ad", "email", "search", "direct"], entry["channel"]),
          f"channel = {entry['channel_label']}", entry["why"])

    # 2 · ad variant (only meaningful on a paid click)
    is_ad = entry["channel"] == "ad"
    intent = _campaign_intent(entry.get("utm_campaign"))
    ad_taken = ("catalogued variant" if ad else
                ("campaign keyword intent" if intent else "no match") if is_ad else None)
    stage("advariant", "Ad variant resolve", "#sec-entry",
          [f"utm_campaign={sig.get('utm_campaign', '—')}", f"utm_content={sig.get('utm_content', '—')}"],
          "AD_BY_VARIANT_ID / AD_BY_CAMPAIGN lookup, else keyword intent",
          _branches(["catalogued variant", "campaign keyword intent", "no match"], ad_taken),
          (f"{ad['id']} · {ad['x_targeting_type']}" if ad
           else (f"intent = {intent}" if is_ad and intent else "generic ad framing" if is_ad else "—")),
          "a catalogued X variant message-matches every copy slot to the ad promise",
          skipped=not is_ad, skip_reason="not a paid click — no ad promise to match")

    # 3 · IP resolve → network type
    firmo = " · ".join(x for x in (
        f"company={det.get('company')}" if det.get("company") else "",
        f"region={det.get('region')}" if det.get("region") else "",
        f"industry={_ind_label(det)}" if _ind_label(det) else "") if x) or "no firmographics"
    stage("ip", "IP resolve + classify", "#sec-tier",
          [f"ip={det.get('ip') or '—'}" + (" (?ip= override)" if P.get("ip_forced") else ""),
           f"isp={det.get('isp') or '—'}"],
          "reverse-IP (ip-api) → network flags → deterministic router (scene._classify)",
          _branches(NETWORK_BRANCHES, det.get("network_type") or "private / unreachable"),
          firmo, det.get("reason") or "network flags decide how much the IP is allowed to imply")

    # 4 · tier route
    conf = P["confidence"]
    stage("tier", "Tier route", "#sec-tier",
          [f"confidence: location={conf['location']} · company={conf['company']} · industry={conf['industry']}"],
          "industry resolved → 2 · geo only → 1 · nothing usable → 0",
          _branches([f"{k} · {v}" for k, v in SC.TIER_LABELS.items()],
                    f"{P['tier']} · {P['tier_label']}"),
          f"tier {P['tier']} · {P['tier_label']}",
          "the tier gates which copy path runs — never what we recite")

    # 5 · identity
    id_taken = ("cohort CRM" if ident and ident["kind"] == "cohort"
                else "work-email resolved" if ident and ident["kind"] == "resolved"
                else "anonymous")
    stage("identity", "Identity", "#sec-crm",
          [f"cookie={'set' if ident and ident.get('via') == 'login' else '—'}",
           f"magic token={'present' if entry['token'] else '—'}"],
          "cohort.match(email) / by_token(e), else resolve_email() first-party domain",
          _branches(["cohort CRM", "work-email resolved", "anonymous"], id_taken),
          (f"{ident['email']} via {ident['via']}" if ident else "anonymous"),
          ("they identified themselves — say-level facts unlock; enrichment stays allude/hold"
           if ident else "no identity offered — nothing personal may be said"))

    # 6 · segments → archetype (cohort only)
    is_cohort = bool(ident and ident["kind"] == "cohort")
    stage("archetype", "Segments → archetype", "#sec-crm",
          ([f"{fam}: " + ", ".join(s["label"] for s in d["segments"])
            for fam, d in ident["segments"].items()] if is_cohort else ["(no CRM record)"]),
          "segments.derive() → pick_archetype()",
          _branches([a["label"] for a in SEG.ARCHETYPES.values()],
                    ident["archetype"]["label"] if is_cohort else None),
          (f"archetype = {ident['archetype']['label']}" if is_cohort else "—"),
          ("behavioral + enriched segments choose emphasis and section order — never recited"
           if is_cohort else ""),
          skipped=not is_cohort, skip_reason="no CRM record — no segments to derive")

    # 7 · audience route
    stage("audience", "Audience route", "#sec-order",
          [P["audience_rule"]],
          "precedence: ad variant > campaign intent > CRM > work-email domain > network type",
          _branches(["companies", "individuals", "neutral"], P["audience"]),
          f"audience = {P['audience']}",
          "companies → Hire/Catalyst emphasis; individuals → Challenger emphasis")

    # 8 · objection prioritize (includes the narrower track route)
    pri = P["objections"]["prioritized"]
    stage("objections", "Objection prioritize", "#sec-objections",
          [f"track route = {ROUTE_LABELS.get(P['audience_route'], P['audience_route'])}"]
          + ([f"#{r['rank']} {r['objection_id']} (score {r['score']})" for r in pri] or ["no signals matched"]),
          "score OBJECTION_CATALOG signals → rank top 3–5 → weave into copy slots",
          _branches(list(ROUTE_LABELS.values()),
                    ROUTE_LABELS.get(P["audience_route"], P["audience_route"])),
          (f"{len(pri)} objections ranked" if pri else "no objections matched"),
          "sales psychology meets them where they are — every reframe uses only site claims")

    # 9 · surface policy gate — per-slot say / allude / hold
    diff = P["copy_diff"]
    changed = [d for d in diff if d["changed"]]
    n_say = sum(1 for d in changed if d["policy"] == "say")
    n_allude = sum(1 for d in changed if d["policy"] == "allude")
    n_blocked = (sum(1 for d in diff if d.get("blocked_say"))
                 + len(P["objections"]["blocked"]))
    stage("policy", "Surface policy gate", "#sec-slots",
          [f"{d['slot']}: {d['policy']}" for d in changed] or ["(all slots generic)"],
          "say = recite · allude = shape only · hold = never ships",
          [{"label": f"say — recited ({n_say})", "taken": n_say > 0},
           {"label": f"allude — shaped ({n_allude})", "taken": n_allude > 0},
           {"label": f"hold — blocked ({n_blocked})", "taken": n_blocked > 0}],
          f"{len(changed)} of {len(diff)} slots personalized · {n_blocked} say variants blocked",
          "every personalized slot carries its source + policy; blocked recites appear only on /dev")

    # 10 · compose
    stage("compose", "Compose page", "#sec-order",
          [f"audience = {P['audience']}"
           + (f" · ad variant order override ({ad['id']})" if ad and ad["page"].get("order") else "")],
          "ORDER_BY_AUDIENCE, unless the ad variant overrides",
          [],
          " → ".join(P["order"]),
          "same sections, same facts — only emphasis and order move")

    # 11 · hero image
    hi = P["hero_image"]
    ir = hi.get("receipt") or {}
    hid = hi.get("dev") or {}
    sel = hid.get("intent_selection") or {}
    src = ir.get("source", "gradient")
    hi_reads = [
        f"status={hi.get('status', 'ready')}",
        f"fallback={hi.get('fallback', 'gradient')}",
        f"intent={ir.get('intent_id', '—')}",
    ]
    if sel.get("rule_fired"):
        hi_reads.append(f"rule={sel['rule_fired'][:48]}")
    if ir.get("drives_action"):
        hi_reads.append(f"drives_action={ir['drives_action']}")
    blocked = ir.get("guardrails_blocked") or []
    if blocked:
        hi_reads.append(f"guardrails_blocked={len(blocked)}")
    stage("heroimg", "Hero image resolve", "#sec-hero-image",
          hi_reads,
          "select_image_intent → build_structured_prompt → guardrails → cache → API → gallery → gradient",
          _branches(["generated", "pending", "gallery", "gradient"], src),
          f"source = {src} · intent = {ir.get('intent_id', '—')}",
          (f"intent {ir.get('intent_id')} ({ir.get('conversion_goal', '—')}) drives hero CTA; "
           f"{len(blocked)} guardrail(s) applied" if blocked else
           "structured prompt assembled from signals — page shell renders instantly"))

    return {"inputs": inputs, "stages": stages}


def sample_login_email() -> str:
    """The cohort email published on the showcase card (synthetic)."""
    return "maya.chen@gauntletai.com"


def sample_magic_token() -> str:
    """The magic token embedded in the sample email entry link (synthetic recipient)."""
    return CO.magic_token(CO.BY_ID["liam"])
