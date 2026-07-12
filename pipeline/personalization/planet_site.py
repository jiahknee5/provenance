"""Planet (planet.com) replica — live entry-point + IP + CRM personalization for /planet (+ /planet/dev).

A pixel-faithful mock of a planet.com-style marketing site whose copy blocks are
personalization SLOTS filled deterministically from the engine the repo already has:

  • classify_entry() — the four entry channels (ad / email / search / direct).
  • scene.detect()/resolve_ip() — the always-on IP layer: network type + tiers 0–3.
  • planet_cohort.match()/by_token() + segments.derive()/pick_archetype() — the known-visitor
    path (login or magic token) → CRM record → archetype → section emphasis + say-level copy.

THE PLANET DIFFERENTIATOR — LOCATION. Planet images every place on Earth's landmass every
day, so the visitor's geography is not merely a tone signal here: it is the product's
truthful superpower claim ("we already image *your* ground daily"). A dedicated location
stage turns geo-IP region × market segment into a hero location line ("Every field in
{region}, imaged today") and steers the hero-image intents — with the anti-surveillance
guardrail: region/landscape scale only, never street or property scale, and defense
audiences get the theater-of-interest register, never their own location.

Surface policy is enforced exactly as the repo defines it: `say` facts may be recited;
`allude` facts only SHAPE copy; `hold` facts never reach the page — the recite variants
appear only on /planet/dev, marked blocked. Deterministic — no LLM, no RNG.

All company facts sourced from docs/research/planet-market-segments.md (verified July 2026).
"""
from __future__ import annotations

from pipeline.personalization import image_gen as IG
from pipeline.personalization import motion_gen as MG
from pipeline.personalization import planet_cohort as CO
from pipeline.personalization import scene as SC
from pipeline.personalization import segments as SEG

IMAGE_TENANT = "planet"

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
    if any(w in c for w in ("defense", "geoint", "sovereign", "tasking", "mission",
                            "maritime", "underwrit", "insurance", "enterprise")):
        return "enterprise"
    if any(w in c for w in ("research", "university", "academic", "study", "education", "science")):
        return "research"
    if any(w in c for w in ("trial", "aum", "monitor", "forestry", "eudr", "energy",
                            "gov", "crisis", "selfserve", "self-serve")):
        return "selfserve"
    return None


# --------------------------------------------------------------------------- #
# X.com ad variants — 12 total = one per real X Ads Manager targeting type,
# built on the nine researched Planet market segments
# (docs/research/planet-market-segments.md §2 + §5).
#
# Categories on /ads + /ads-lp:
#   vertical — six vertical segments matched via geo/delivery-style targeting
#              (agriculture, defense, insurance, forestry, energy, civil government)
#   audience — six audience/behavioral plays (maritime interest, crisis retarget,
#              documentary viewers, broad-reach language, early-career age, all-gender trial)
#
# Each variant carries utm_campaign=x-{slug} and utm_content=v01–v12. Copy follows
# docs/research/copy-personalization-research.md: 60–90 words, one idea, soft CTA,
# loss framing where signal-derived, verified proof points only.
# Age/gender may target in X Ads but the landing page holds those facts — never recited.
# Defense location register: theater-of-interest only — never the visitor's location.
# --------------------------------------------------------------------------- #
AD_CATEGORIES = (
    {"key": "vertical", "label": "Vertical & geo"},
    {"key": "audience", "label": "Audience & intent"},
)

AUDIENCE_FIT = {
    "Agronomy": {"label": "VP Digital Ag / Agronomy", "avatar": "AG", "accent": "#3fa34d"},
    "GEOINT": {"label": "Defense / GEOINT lead", "avatar": "DI", "accent": "#5b6b8c"},
    "Underwriting": {"label": "Claims / Cat-model lead", "avatar": "IN", "accent": "#b5731b"},
    "Carbon/MRV": {"label": "Forest-carbon MRV lead", "avatar": "FC", "accent": "#1e8a53"},
    "Energy Ops": {"label": "Pipeline / asset-integrity lead", "avatar": "EN", "accent": "#c2761a"},
    "Civil Gov": {"label": "State agency / GIS director", "avatar": "CG", "accent": "#0e7490"},
    "Maritime": {"label": "MDA / fisheries enforcement", "avatar": "MA", "accent": "#1e6fa8"},
    "Response": {"label": "Emergency-response GIS lead", "avatar": "DR", "accent": "#8a5cf6"},
    "Research": {"label": "University PI / researcher", "avatar": "ER", "accent": "#0e9bab"},
    "cross-audience": {"label": "Cross-audience", "avatar": "PL", "accent": "#64748b"},
}

_AUDIENCE_ROUTE = {"Agronomy": "enterprise", "GEOINT": "enterprise", "Underwriting": "enterprise",
                   "Maritime": "enterprise",
                   "Carbon/MRV": "selfserve", "Energy Ops": "selfserve", "Civil Gov": "selfserve",
                   "Response": "selfserve",
                   "Research": "research", "cross-audience": "neutral"}


def _v(id_, variant_id, category, segment, audience_fit, x_targeting_type, x_targeting_example,
       utm_campaign, *,
       trigger, body, proof, cta_label,
       h1_pre, h1_blue, sub, hero_eyebrow="",
       cta_primary, cta_secondary,
       compare_emphasis, order=None,
       prove_intro=None, research_body=None, research_hot=False,
       cta_heading=None, cta_sub=None, stat_highlight=None,
       hold_note=None):
    """Build one ad variant dict with paired ad mockup + landing-page overrides."""
    fit = AUDIENCE_FIT[audience_fit]
    return {
        "id": id_,
        "variant_id": variant_id,
        "category": category,
        "segment": segment,
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
            "handle": "planet",
            "display": "Planet",
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
            "h1_blue": h1_blue,
            "sub": sub,
            "cta_primary": cta_primary,
            "cta_secondary": cta_secondary,
            "compare_emphasis": compare_emphasis,
            "order": order,
            "prove_intro": prove_intro,
            "research_body": research_body,
            "research_hot": research_hot,
            "cta_heading": cta_heading,
            "cta_sub": cta_sub,
            "stat_highlight": stat_highlight,
        },
    }


AD_VARIANTS: list[dict] = [
    # --- Vertical & geo (v01–v06) — one per researched vertical segment ---
    _v("x-agriculture", "v01", "vertical", "agriculture", "Agronomy",
       "Location targeting", "Des Moines · Lincoln · Fresno · crop-belt metros",
       "x-location-crop-belts",
       trigger="Every field in the corn belt, imaged today.",
       body=("Your agronomists can't drive two million acres in a season — and cloud "
             "cover keeps breaking everyone else's revisit."),
       proof=("Bayer, Corteva, and Syngenta run on daily 3 m PlanetScope imagery — "
              "field-level crop-stress detection from preseason to harvest, by API."),
       cta_label="See your fields from orbit →",
       hero_eyebrow="You clicked the crop-belt ad",
       h1_pre="Every Field in Your Region, ", h1_blue="Imaged Today",
       sub=("Daily 3 m imagery catches crop stress while you can still act on it — even in "
            "regions with frequent cloud cover. Field-level insight from preseason to "
            "harvest, delivered by simple cloud APIs."),
       cta_primary="Talk to Sales", cta_secondary="Start Free Trial",
       compare_emphasis="monitor",
       prove_intro=("Bayer monitors seed-production fields across four continents on this data. "
                    "Daily revisit means the season never goes dark on you."),
       cta_heading="Your acres are already in today's take",
       cta_sub="Daily 3 m coverage of every field — see this season while it can still change.",
       stat_highlight=0),
    _v("x-defense", "v02", "vertical", "defense", "GEOINT",
       "Follower look-alikes targeting", "Lookalikes of defense & GEOINT accounts",
       "x-lookalike-defense",
       trigger="The theater doesn't pause. Neither does the constellation.",
       body=("Tasked constellations only see where someone pointed them. Daily coverage of "
             "the entire landmass means nothing needs pre-tasking to be in the archive."),
       proof=("NATO signed. Sweden signed. Germany funded €240M of dedicated Pelican "
              "capacity with direct downlink. Sovereign access without building satellites."),
       cta_label="See the mission brief →",
       hero_eyebrow="You clicked the defense ad",
       h1_pre="Indications and Warnings, at the ", h1_blue="Daily Pace of Change",
       sub=("Understand events, anticipate impacts, respond immediately — daily global "
            "coverage plus 30 cm-class tasking, downlinked direct to your ground segment. "
            "AI-triaged monitoring of installations and coastlines at planetary scale."),
       cta_primary="Talk to Sales", cta_secondary="See Satellite Services",
       compare_emphasis="task",
       order=["hero", "prove", "compare", "numbers", "research", "cta"],
       prove_intro=("Daily monitoring finds the change; dedicated tasking inspects it. One "
                    "provider from strategic warning to 30 cm-class look — no constellation to build."),
       cta_heading="Sovereign capability, without the launch program",
       cta_sub="Dedicated capacity, direct downlink, daily global baseline.",
       stat_highlight=1,
       hold_note=("Defense location register: theater-of-interest only — the visitor's own "
                  "location is never referenced (anti-surveillance guardrail)")),
    _v("x-insurance", "v03", "vertical", "insurance", "Underwriting",
       "Event targeting", "RIMS · reinsurance renewals · cat-modeling conferences",
       "x-event-insurance",
       trigger="The 'before' picture of every property in your book already exists.",
       body=("Your adjusters see one roof at a time. AI damage grading from 50 cm tasking "
             "bins whole counties in hours — against a daily archive of the before state."),
       proof=("AXA Climate pays parametric drought claims on 20 years of Planet soil-moisture "
              "data — no ground sensors to maintain, no arguments at payout time."),
       cta_label="See the claims workflow →",
       hero_eyebrow="You clicked the insurance-event ad",
       h1_pre="Claims Triage in Days, ", h1_blue="Not Weeks",
       sub=("Daily archive imagery means the before-picture of every insured property already "
            "exists — post-event tasking grades damage in analytic bins while your competitors "
            "are still scheduling adjusters."),
       cta_primary="Talk to Sales", cta_secondary="Start Free Trial",
       compare_emphasis="monitor",
       prove_intro=("Underwriting and claims both run on the same truth: a continuous, "
                    "sensor-free record of every risk you hold, before and after the event."),
       cta_heading="Underwrite with the archive, settle with the tasking",
       cta_sub="Twenty years of measurements nobody can argue with.",
       stat_highlight=0),
    _v("x-forestry", "v04", "vertical", "forestry", "Carbon/MRV",
       "Conversation targeting", "Threads about EUDR · carbon credits · MRV",
       "x-conversation-eudr",
       trigger="EUDR enforcement lands December 2026. Is your supply shed clean?",
       body=("Plot-level deforestation checks against daily imagery, audit-ready — and "
             "tree-scale carbon baselines that credit buyers actually believe."),
       proof=("Forest Carbon Diligence covers the globe back to 2013; Forest Carbon Monitoring "
              "resolves change at 3 m tree scale. NICFI partners use it to reverse tropical forest loss."),
       cta_label="Check your supply shed →",
       hero_eyebrow="You clicked the EUDR-conversation ad",
       h1_pre="Baselines Buyers ", h1_blue="Believe",
       sub=("Deforestation alerts are only useful before the clearing finishes. Daily revisit "
            "catches degradation while it's still small — and tree-scale canopy height, cover, "
            "and carbon make your MRV audit-ready."),
       cta_primary="Start Free Trial", cta_secondary="Talk to Sales",
       compare_emphasis="monitor",
       prove_intro=("The world's first tree-scale global forest monitoring system, on top of a "
                    "daily archive that reaches back a decade — evidence, not estimates."),
       cta_heading="Prove the forest is still standing",
       cta_sub="Plot-level checks against daily imagery, audit-ready.",
       stat_highlight=0),
    _v("x-energy", "v05", "vertical", "energy", "Energy Ops",
       "Keyword targeting", "\"pipeline integrity\" · \"methane monitoring\" · \"tailings dam\"",
       "x-keyword-energy",
       trigger="Every mile of right-of-way, checked from orbit.",
       body=("Daily imagery flags encroachment before the dig crew shows up — and 400-band "
             "hyperspectral makes your methane obligations visible from space."),
       proof=("Freeport-McMoRan monitors tailings dams daily without walking the crest. "
              "Engineers stay safe; models stay calibrated."),
       cta_label="See asset monitoring →",
       hero_eyebrow="You clicked the keyword-targeted ad",
       h1_pre="Stop Walking Assets You Can ", h1_blue="Watch From Orbit",
       sub=("Oversee assets, monitor competition, mitigate disaster — daily imagery over every "
            "corridor and site reduces dangerous, costly manual inspection, and Tanager "
            "hyperspectral detects and quantifies methane plumes at the source."),
       cta_primary="Start Free Trial", cta_secondary="Talk to Sales",
       compare_emphasis="monitor",
       order=["hero", "compare", "prove", "numbers", "research", "cta"],
       prove_intro=("Encroachment, tailings, construction progress, methane — one daily feed "
                    "replaces a fleet of trucks and flights."),
       cta_heading="Your operating basin, every day",
       cta_sub="Daily coverage flags the change before it becomes the incident.",
       stat_highlight=1),
    _v("x-government", "v06", "vertical", "government", "Civil Gov",
       "Device, platform, & Wi-Fi targeting", "Desktop · office hours · state networks",
       "x-device-civgov",
       trigger="Your whole state, imaged daily.",
       body=("You can't field-inspect every parcel — but you can watch all of them. AI change "
             "detection flags fire, flood, and unpermitted activity across the jurisdiction."),
       proof=("One state forestry division digitizes wildfire perimeters in minutes and cut "
              "investigation costs $160,000 by replacing helicopter recon."),
       cta_label="See the government workflow →",
       hero_eyebrow="You clicked the civil-government ad",
       h1_pre="Fire Perimeters in Minutes, ", h1_blue="Not Helicopter Hours",
       sub=("Broad area management for jurisdictions too big to drive: near-daily imagery "
            "replaced aerial recon for one state agency and cut investigation costs $160K. "
            "Your whole county — every parcel, every day."),
       cta_primary="Start Free Trial", cta_secondary="Talk to Sales",
       compare_emphasis="monitor",
       prove_intro=("Monitoring, measuring, and reporting on changes to natural and human-made "
                    "assets over vast areas — with shrinking field-staff budgets in mind."),
       cta_heading="Watch the whole jurisdiction",
       cta_sub="Fire, flood, permits — flagged by change detection, verified by your team.",
       stat_highlight=2),
    # --- Audience & intent (v07–v12) ---
    _v("x-maritime", "v07", "audience", "maritime", "Maritime",
       "Interest targeting", "Maritime security · shipping · ocean conservation",
       "x-interest-maritime",
       trigger="AIS off doesn't mean invisible.",
       body=("Deep-learning vessel detection across 20 million sq km of open water, "
             "near-daily — classification, ship-to-ship transfers, and the wakes with no "
             "transponder attached."),
       proof=("The North Korea dark-fleet exposé found ~800 illegal pair trawlers from orbit "
              "— published in Science Advances. That methodology is a product."),
       cta_label="See vessel detection →",
       hero_eyebrow="You clicked the maritime-interest ad",
       h1_pre="Dark Vessels, ", h1_blue="Found From Orbit",
       sub=("Survey waters, detect vessels, track activity — near-daily 3.7 m imagery over "
            "20 million sq km of strategic water, fused with AIS to turn anecdotes into "
            "evidence for enforcement and underwriting."),
       cta_primary="Talk to Sales", cta_secondary="Start Free Trial",
       compare_emphasis="task",
       prove_intro=("Automated Vessel Detection classifies cargo, tanker, and military traffic "
                    "and flags ship-to-ship transfers — over waters no patrol can cover daily."),
       cta_heading="Every port call, on the record",
       cta_sub="Daily imaging plus AIS fusion — the dark fleet has nowhere left to fish.",
       stat_highlight=1),
    _v("x-disaster", "v08", "audience", "disaster", "Response",
       "Post Engager targeting", "Engaged with @planet crisis-response posts (last 30 days)",
       "x-engager-crisis",
       trigger="You followed our crisis-response work — here's the promise behind it.",
       body=("Roads close. Comms drop. Orbits don't. Before/after imagery of any place on "
             "Earth within hours — because we imaged it yesterday, too."),
       proof=("LA County wildfires, Brazil floods: qualified responders get crisis imagery at "
              "no cost through the Disaster Data program."),
       cta_label="Pick up where you left off →",
       hero_eyebrow="Welcome back from X",
       h1_pre="The First Map, ", h1_blue="By Sunrise",
       sub=("In the first 72 hours, situational awareness is the scarcest resource. Daily "
            "global imaging gives responders the before/after pair on day one — when roads "
            "and comms are down and the damage assessment can't wait."),
       cta_primary="Start Free Trial", cta_secondary="See Disaster Data",
       compare_emphasis="task",
       order=["hero", "prove", "compare", "numbers", "research", "cta"],
       prove_intro=("Founded to use space to help life on Earth — the Crisis Response Program "
                    "releases imagery for major disasters at no cost to qualified responders."),
       cta_heading="Ready before the water rises",
       cta_sub="The before-picture that makes damage assessment instant.",
       stat_highlight=0),
    _v("x-docs", "v09", "audience", "research", "Research",
       "Movies & TV targeting", "Space & Earth-science documentaries · nature series",
       "x-movies-earth-docs",
       trigger="If you've watched every Earth-from-space documentary and still run models on 16-day revisit —",
       body=("Daily 3 m imagery since 2016 for time-series science. Landsat gives you 16 days. "
             "Sentinel gives you 5. We give you 1."),
       proof=("10,000+ researchers at 1,000+ universities publish about two papers a day on "
              "this data — free for university research."),
       cta_label="Apply for research access →",
       hero_eyebrow="You clicked the documentary-viewer ad",
       h1_pre="Stop Watching Earth. ", h1_blue="Start Measuring It.",
       sub=("The Education & Research Program puts the world's densest EO time series behind "
            "your science — daily 3 m imagery, publication-grade licensing, free for "
            "non-commercial university research."),
       cta_primary="Apply for Research Access →", cta_secondary="Start Free Trial",
       compare_emphasis="monitor",
       research_hot=True,
       research_body=("Apply to the Education & Research Program — free non-commercial access, "
                      "3,000 sq km/month on the Basic tier, SkySat tasking included. "
                      "1,000+ universities already on it."),
       prove_intro=("Time-series science lives or dies on cadence. A daily archive back to 2016 "
                    "turns aliased signals into measurements."),
       cta_heading="Your turn to be the citation",
       cta_sub="Two papers a day are published on this data. Free for university research.",
       stat_highlight=0),
    _v("x-broad", "v10", "audience", "cross", "cross-audience",
       "Language targeting", "English (United States) — broad awareness",
       "x-language-en-us",
       trigger="Most of Earth changes faster than anyone re-checks it.",
       body=("Planet images the entire landmass every day at 3 m — change made visible, "
             "accessible, and actionable, from crop stress to coastlines."),
       proof=("897 direct customers, from Bayer to NATO to Global Fishing Watch. "
              "$307.7M FY26 revenue and a record $900M backlog."),
       cta_label="Worth a look? →",
       hero_eyebrow="You clicked the broad-reach ad",
       h1_pre="See the Whole World Change, ", h1_blue="Daily",
       sub=("The largest Earth-observation fleet in orbit images every place on Earth's "
            "landmass every day — so whatever ground you manage, the archive already "
            "holds years of it."),
       cta_primary="Talk to Sales", cta_secondary="Start Free Trial",
       compare_emphasis="monitor",
       prove_intro=("Look broader with daily monitoring, closer with 50 cm tasking, deeper "
                    "with hyperspectral — one platform from pixels to decisions."),
       cta_heading="Your geography is already in the archive",
       cta_sub="Daily coverage means the before-picture always exists.",
       stat_highlight=2),
    _v("x-age", "v11", "audience", "research", "Research",
       "Age targeting", "25–44 (grad students & early-career analysts)",
       "x-age-early-career",
       trigger="Early-career researchers tell us the same thing: the archive made the dissertation.",
       body=("Your study area, imaged daily since 2016 — the densest EO time series there is, "
             "free for university research."),
       proof=("Basic tier covers 3,000 sq km a month. Approval in under three weeks. SkySat "
              "tasking now included — a first for a university program."),
       cta_label="Apply for access →",
       hero_eyebrow="You clicked the early-career researcher ad",
       h1_pre="Your Study Area, ", h1_blue="Every Day Since 2016",
       sub=("Free academic access to the world's densest Earth-observation time series — "
            "daily 3 m imagery of your field sites, publication-grade licensing, campus "
            "licenses for whole institutions."),
       cta_primary="Apply for Research Access →", cta_secondary="See the Science Program",
       compare_emphasis="monitor",
       order=["hero", "research", "prove", "compare", "numbers", "cta"],
       research_hot=True,
       research_body=("Apply to the Education & Research Program — approval typically inside "
                      "three weeks, quota that covers a real study area, and an archive that "
                      "reaches back to 2016."),
       prove_intro=("Researchers think in AOIs. Daily revisit of yours — since 2016 — is the "
                    "difference between a trend and a finding."),
       cta_heading="The archive is your instrument",
       cta_sub="Daily 3 m imagery for time-series science, free for university research.",
       stat_highlight=0,
       hold_note="Age targets in X Ads (25–44) but the landing page holds age — never recited (surface policy)"),
    _v("x-gender", "v12", "audience", "cross", "cross-audience",
       "Gender targeting", "All genders (broad reach)",
       "x-gender-all",
       trigger="The planet doesn't care who's watching — but everyone should get to.",
       body=("Broad reach, one promise: daily imagery of every place on Earth's landmass, "
             "with a 30-day free trial and no credit card."),
       proof=("Sandbox data, public Sentinel and Landsat archives, and 30,000 processing "
              "units to prove it on your own geography."),
       cta_label="Start the trial →",
       hero_eyebrow="You clicked the Planet ad",
       h1_pre="Prove It on ", h1_blue="Your Own Geography",
       sub=("Don't take our word for your ground — the 30-day free trial opens the Insights "
            "Platform on your own area of interest, no credit card, sandbox included."),
       cta_primary="Start Free Trial", cta_secondary="Talk to Sales",
       compare_emphasis="monitor",
       prove_intro=("Self-serve Area Under Management subscriptions and Single Order Tasking "
                    "mean the smallest team can buy exactly the acres it manages."),
       cta_heading="Thirty days, your AOI, no card",
       cta_sub="The fastest way to believe it is to watch your own ground change.",
       stat_highlight=2,
       hold_note="Gender may target in X Ads but the landing page holds gender — never recited (surface policy)"),
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


def variant_landing_url(variant: dict, page_path: str = "/planet") -> str:
    """Full landing-page URL with the variant's UTM params."""
    q = (f"utm_source={variant['utm_source']}&utm_medium={variant['utm_medium']}"
         f"&utm_campaign={variant['utm_campaign']}&utm_content={variant['variant_id']}")
    return f"{page_path}?{q}"


def ad_grid_sections() -> list[dict]:
    """Grouped grid data for /ads + /ads-lp: two categories × 6 variants each."""
    by_cat: dict[str, list[dict]] = {c["key"]: [] for c in AD_CATEGORIES}
    for v in AD_VARIANTS:
        by_cat[v["category"]].append(v)
    return [{"category": c["key"], "label": c["label"], "variants": by_cat[c["key"]]}
            for c in AD_CATEGORIES]


def generic_hero_headline() -> str:
    return GENERIC["hero"]["h1_pre"] + GENERIC["hero"]["h1_blue"]


def variant_hero_headline(variant: dict) -> str:
    p = variant["page"]
    return p["h1_pre"] + p["h1_blue"]


# --------------------------------------------------------------------------- #
# The generic page — real planet.com claims (verified 2026-07, see research doc).
# Nothing invented: every number and phrase traces to planet.com / SEC filings.
# --------------------------------------------------------------------------- #
GENERIC = {
    "hero": {
        "eyebrow": "",
        "h1_pre": "Image the World ", "h1_blue": "Every Day",
        "sub": ("Planet operates the largest Earth-observation fleet in orbit — daily 3 m "
                "imagery of Earth's entire landmass that makes change visible, accessible, "
                "and actionable."),
        "cta_primary": "Talk to Sales", "cta_secondary": "Start Free Trial",
        "location_line": "",
    },
    "prove": {
        "h_pre": "How We Make Change ", "h_blue": "Visible",
        "intro": ("Daily monitoring of the entire landmass, high-resolution tasking on demand, "
                  "and analysis-ready feeds — look broader, closer, and deeper without "
                  "building a constellation."),
    },
    "research": {
        "eyebrow": "For Researchers & Students", "heading": "Your Study Area, Daily Since 2016",
        "body": ("Apply to the Education & Research Program — free non-commercial access up to "
                 "3,000 sq km/month, used at 1,000+ universities in 100+ countries."),
        "cta": "Apply for Research Access →",
    },
    "cta": {
        "heading": "See your world change daily",
        "sub": "Every place on Earth, imaged every day. Your geography is already in the archive.",
        "cta_primary": "Talk to Sales", "cta_secondary": "Start Free Trial",
    },
}

PROVE_CARDS = [
    ("Daily, Everywhere", "PlanetScope images Earth's entire landmass every day at 3 m — "
                          "nothing needs pre-tasking to be in the archive."),
    ("Broader, Closer, Deeper", "Daily monitoring cues 50 cm SkySat and 30 cm-class Pelican "
                                "tasking, and 400-band Tanager hyperspectral quantifies what "
                                "optical alone can't."),
    ("A Decade of Before-Pictures", "Years of daily history over any area of interest — a "
                                    "time machine no tasked constellation can backfill."),
    ("Data to Decisions", "Analysis-ready Planetary Variables, AI-powered detection, and "
                          "cloud APIs that plug into ArcGIS, QGIS, and your stack."),
]

COMPARE_ROWS = [
    ("Constellation", "PlanetScope — ~200 SuperDoves", "SkySat + Pelican — ~21 sats and growing"),
    ("Resolution", "3 m, 8 spectral bands (SuperRes to 2 m)", "50 cm today; 30 cm-class Pelican"),
    ("Revisit", "Every day, entire landmass", "Sub-daily, on demand"),
    ("Best for", "Broad area management — watching everything, alerting on change",
     "Inspecting a known target closely, right now"),
    ("Coverage", "All of Earth's landmass, automatically", "Your tasked area of interest"),
    ("Archive", "Daily history back to 2016", "Tasked captures only"),
    ("Delivery", "APIs, Insights Platform, Planetary Variables feeds",
     "Single Order Tasking, direct-downlink options"),
    ("Pricing motion", "Self-serve AUM from ~$2,700/yr, or enterprise license",
     "Per-task orders or dedicated satellite services"),
    ("Next step", "Start a 30-day free trial", "Talk to sales about tasking"),
]

NUMBERS = [("3 m · daily", "Earth's entire landmass, imaged every day"),
           ("200+", "SuperDoves + 21 SkySats — the largest EO fleet in orbit"),
           ("897", "Direct customers, from Bayer to NATO")]

TRUSTED_BY = ["Bayer", "NATO", "AXA Climate", "Global Fishing Watch", "Corteva", "Freeport-McMoRan"]

# real-site section order — reorders per audience, structure never changes
DEFAULT_ORDER = ["hero", "prove", "research", "compare", "numbers", "cta"]
ORDER_BY_AUDIENCE = {
    "enterprise": ["hero", "prove", "compare", "numbers", "research", "cta"],
    "selfserve": ["hero", "compare", "prove", "numbers", "research", "cta"],
    "research": ["hero", "research", "prove", "compare", "numbers", "cta"],
    "neutral": DEFAULT_ORDER,
}

# --------------------------------------------------------------------------- #
# LOCATION — the Planet differentiator. Region (geo-IP, tier-gated) × segment →
# a truthful hero location line. Guardrails: region scale only, never street or
# property scale; defense gets the theater-of-interest register, never the
# visitor's own location. (research doc §4)
# --------------------------------------------------------------------------- #
LOCATION_LINES = {
    "agriculture": "Every field in {region}, imaged today.",
    "insurance": "The 'before' picture of every property in {region} already exists.",
    "government": "Your whole {region}, imaged every day.",
    "energy": "Every corridor and site across {region}, checked from orbit.",
    "forestry": "Every hectare of canopy in {region}, revisited daily.",
    "maritime": "The waters off {region}, surveyed near-daily.",
    "disaster": "When {region} floods, the first map matters most — the before-picture is already in the archive.",
    "research": "{region} study sites, imaged daily since 2016.",
}
DEFAULT_LOCATION_LINE = "Planet imaged {region} today — and every day for the past decade."
THEATER_LINE = "Daily coverage over the theaters your mission watches — never over you."


def location_signal(det: dict, tier: int, ad_variant: dict | None) -> dict:
    """Deterministic location decision: {line, mode, rule, policy, why, blocked_say, segment}."""
    seg = ad_variant["segment"] if ad_variant else None
    region, city = det.get("region"), det.get("city")
    if seg == "defense":
        return {"line": THEATER_LINE, "mode": "theater", "segment": seg, "region": None,
                "rule": "segment=defense → theater-of-interest register (guardrail)",
                "policy": "allude",
                "why": ("defense audiences reference their regional security theater, never their "
                        "own location — daily-coverage confidence, not surveillance"),
                "blocked_say": (f"Our satellites passed over {city or region} this morning — "
                                "here's your facility" if region else None)}
    if tier >= 1 and region:
        template = LOCATION_LINES.get(seg or "", DEFAULT_LOCATION_LINE)
        return {"line": template.format(region=region), "mode": "region", "segment": seg,
                "region": region,
                "rule": f"tier ≥ 1 + region resolved → segment template ({seg or 'default'})",
                "policy": "allude",
                "why": ("Planet's truthful superpower claim: every place on Earth's landmass is "
                        "imaged daily, so the visitor's region IS in today's take — region scale "
                        "only, never street or property scale"),
                "blocked_say": (f"We can see you're browsing from {city + ', ' if city else ''}"
                                f"{region} right now — here's your building from orbit")}
    return {"line": "", "mode": "none", "segment": seg, "region": None,
            "rule": "tier 0 or no region — no location claim ships",
            "policy": "hold",
            "why": "no location confidence (VPN / hosting / private IP) — a wrong region claim "
                   "would break the exact trust the daily-coverage claim builds",
            "blocked_say": None}


def brain_sim_signal(receipt: dict, *, tenant: str = IMAGE_TENANT) -> dict:
    """Brain-simulator decision summary for /planet/dev trace, process map, and panels."""
    from pipeline.personalization import image_intents as II
    from pipeline.personalization.brain_simulator import (
        BRAIN_TARGET_LABELS,
        BRAIN_TARGET_REGIONS,
        brain_sim_enabled,
        intent_brain_fields,
    )

    config = II.load_image_config(tenant)
    enabled = brain_sim_enabled(config)
    intent_id = receipt.get("intent_id")
    target = receipt.get("brain_target")
    regions = list(receipt.get("brain_regions") or [])
    if intent_id and not target:
        for intent in config.get("intents") or []:
            if intent["id"] == intent_id:
                target, regions = intent_brain_fields(intent)
                if target and not regions:
                    regions = list(BRAIN_TARGET_REGIONS.get(target, []))
                break
    score = receipt.get("brain_score")
    simulator = receipt.get("brain_simulator")
    evaluated = receipt.get("candidates_evaluated")
    region_scores = receipt.get("brain_region_scores") or {}
    target_label = BRAIN_TARGET_LABELS.get(target or "", target or "—")

    if not enabled:
        return {
            "enabled": False,
            "mode": "disabled",
            "intent_id": intent_id,
            "brain_target": target,
            "brain_target_label": target_label,
            "brain_regions": regions,
            "brain_simulator": None,
            "brain_score": None,
            "brain_region_scores": {},
            "candidates_evaluated": None,
            "rule": "brain_simulator.enabled: false in tenant YAML",
            "policy": "observed",
            "output": "brain scoring disabled for this tenant",
            "why": "opt-in via brain_simulator.enabled in rules/*_image.yaml",
        }

    if score is not None:
        mode = "scored"
        top_regions = ", ".join(
            f"{k}={v:.2f}" for k, v in sorted(
                region_scores.items(), key=lambda x: -x[1])[:3])
        output = (f"brain_score = {score:.3f} · {simulator or 'proxy_v1'}"
                  + (f" · N={evaluated}" if evaluated else ""))
        why = ("generate → score → select: best-of-N candidates scored against "
               f"brain_target={target} cortical regions; winner cached"
               + (f" ({top_regions})" if top_regions else ""))
    elif target:
        mode = "target_mapped"
        output = f"brain_target = {target} ({target_label}) · intent {intent_id or '—'}"
        why = ("intent YAML maps to a marketing brain_target; scoring runs on generation "
               "(async API default N=3; pregen uses BRAIN_SIM_BEST_OF_N)")
    else:
        mode = "pending"
        output = "no brain_target — gradient / gallery fallback"
        why = "no structured intent resolved — brain simulator not invoked"

    return {
        "enabled": True,
        "mode": mode,
        "intent_id": intent_id,
        "brain_target": target,
        "brain_target_label": target_label,
        "brain_regions": regions,
        "brain_simulator": simulator,
        "brain_score": score,
        "brain_region_scores": region_scores,
        "candidates_evaluated": evaluated,
        "rule": "intent brain_target → BrainSimulatorScorer.select_best() on generate",
        "policy": "observed",
        "output": output,
        "why": why,
    }


# --------------------------------------------------------------------------- #
# Objection catalog — sales psychology, truth-bounded (verified Planet claims only)
# Each objection: id, text, tracks[], weight_signals[], reframe slots, optional blocked_say.
# --------------------------------------------------------------------------- #
TRACKS = ("enterprise", "selfserve", "research")

_AD_SIGNAL = {v["id"]: f"ad_{v['id'].replace('x-', '')}" for v in AD_VARIANTS}

OBJECTION_CATALOG: list[dict] = [
    # --- Enterprise / mission ---
    {"id": "tasked_competitor",
     "text": "Maxar or Airbus already give us 30 cm tasking",
     "tracks": ["enterprise"],
     "signals": [("ad_defense", 14), ("ad_maritime", 9), ("audience_fit_geoint", 10),
                 ("audience_route_enterprise", 7), ("network_corporate", 5)],
     "reframe": {
         "hero_sub": ("30 cm tasking only sees where someone pointed it. Daily coverage of the "
                      "entire landmass means the before-picture already exists — and Pelican "
                      "adds the 30 cm-class look when you need it."),
         "prove_card": (2, "A tasked archive holds only what someone thought to order. A daily "
                        "archive holds everything — including the thing nobody predicted."),
         "compare_row": "Archive",
     }},
    {"id": "sovereignty",
     "text": "We need sovereign capability, not a subscription",
     "tracks": ["enterprise"],
     "signals": [("ad_defense", 12), ("audience_fit_geoint", 12), ("seniority_exec", 6),
                 ("network_corporate", 5)],
     "reframe": {
         "hero_sub": ("Sovereign capability doesn't require building satellites — dedicated "
                      "Pelican capacity with direct downlink to your ground segment is how "
                      "Germany, Ukraine, and Sweden did it."),
         "compare_row": "Delivery",
         "compare_emphasis": "task",
         "final_cta_sub": "Dedicated capacity, direct downlink, your ground segment.",
     },
     "blocked_say": "We resolved your agency from its netblock — here's the desk officer we'd call first"},
    {"id": "resolution_doubt",
     "text": "3 m is too coarse for our use case",
     "tracks": ["enterprise", "selfserve"],
     "signals": [("ad_defense", 8), ("ad_maritime", 8), ("ad_energy", 7), ("ad_insurance", 6),
                 ("audience_route_enterprise", 6), ("tier_2", 4)],
     "reframe": {
         "hero_sub": ("3 m daily monitoring finds the change; 50 cm SkySat and 30 cm-class "
                      "Pelican tasking inspect it. One constellation watches everything, "
                      "another looks closer — the same platform runs both."),
         "prove_card": (1, "Monitoring cues tasking automatically — you never pay high-res "
                        "prices to stand watch."),
         "compare_row": "Resolution",
     }},
    {"id": "procurement_risk",
     "text": "Commercial imagery vendors are a procurement risk",
     "tracks": ["enterprise"],
     "signals": [("ad_defense", 8), ("ad_insurance", 7), ("seniority_exec", 8),
                 ("audience_route_enterprise", 6), ("network_corporate", 5)],
     "reframe": {
         "hero_sub": ("897 direct customers, a $900M backlog, the NRO's EOCL program, and a "
                      "first full year of profitability — the procurement-risk argument is "
                      "aging fast."),
         "compare_row": "Pricing motion",
         "final_cta_sub": "Public company, public numbers, nine-figure government contracts.",
     }},
    {"id": "data_overload",
     "text": "We don't have analysts for more imagery",
     "tracks": ["enterprise", "selfserve"],
     "signals": [("ad_government", 9), ("ad_maritime", 8), ("ad_energy", 7),
                 ("audience_fit_civgov", 8), ("tier_2", 4)],
     "reframe": {
         "hero_sub": ("More pixels aren't the product — answers are. Analysis-ready Planetary "
                      "Variables, AI vessel and change detection, and APIs that land in ArcGIS "
                      "and QGIS mean analysts triage alerts, not scenes."),
         "prove_card": (3, "AI triage turns a daily planet of pixels into a short list of "
                        "changes worth a human's time."),
         "compare_row": "Delivery",
     }},
    {"id": "cloud_cover",
     "text": "Cloud cover makes optical unreliable",
     "tracks": ["enterprise", "selfserve"],
     "signals": [("ad_agriculture", 14), ("ad_forestry", 8), ("audience_fit_agronomy", 10),
                 ("industry_resolved", 5)],
     "reframe": {
         "hero_sub": ("Cloud cover breaks 5-day revisit, not daily revisit — today's miss is "
                      "tomorrow's capture, and 20-year soil-moisture feeds see through clouds "
                      "entirely."),
         "prove_card": (0, "200+ satellites mean the constellation gets another look at every "
                        "field every single day — clouds lose the war of attrition."),
         "compare_row": "Revisit",
     }},
    {"id": "verification_trust",
     "text": "Regulators and buyers won't accept satellite evidence",
     "tracks": ["enterprise", "selfserve"],
     "signals": [("ad_forestry", 12), ("ad_insurance", 9), ("audience_fit_mrv", 10),
                 ("audience_fit_underwriting", 8)],
     "reframe": {
         "hero_sub": ("Satellite evidence already survives scrutiny: a Science Advances paper "
                      "found ~800 dark trawlers with it, AXA pays parametric claims on it, and "
                      "a state agency cut investigation costs $160K with it."),
         "prove_card": (2, "Evidence buyers and courts accept starts with a record nobody could "
                        "have fabricated after the fact — a daily archive is exactly that."),
         "compare_row": "Archive",
     }},
    {"id": "integration_cost",
     "text": "Integration will take us quarters",
     "tracks": ["selfserve", "enterprise"],
     "signals": [("ad_energy", 9), ("ad_government", 7), ("audience_route_selfserve", 8),
                 ("network_corporate", 4)],
     "reframe": {
         "hero_sub": ("The Insights Platform is cloud-native with ArcGIS and QGIS integrations "
                      "— the 30-day trial has teams streaming imagery into existing workflows "
                      "the same afternoon."),
         "compare_row": "Next step",
         "compare_emphasis": "monitor",
     }},
    # --- Self-serve / AUM ---
    {"id": "price_opacity",
     "text": "Satellite data is enterprise-priced — out of our budget",
     "tracks": ["selfserve", "research"],
     "signals": [("archetype_cost_confident", 12), ("preferential_cost", 10), ("ad_forestry", 6),
                 ("audience_route_selfserve", 7)],
     "reframe": {
         "hero_sub": ("Satellite data used to mean enterprise sales calls. Self-serve Area "
                      "Under Management starts around $2,700 a year over your own AOI — and "
                      "the 30-day trial needs no credit card."),
         "compare_row": "Pricing motion",
         "compare_emphasis": "monitor",
         "final_cta_sub": "Your AOI, your budget — start with the trial.",
     },
     "blocked_say": "We modeled your budget band and pre-picked a subscription tier — checkout is one click"},
    {"id": "aoi_small",
     "text": "Our area of interest is too small to justify satellites",
     "tracks": ["selfserve"],
     "signals": [("ad_forestry", 8), ("ad_government", 7), ("audience_route_selfserve", 9),
                 ("network_residential", 4)],
     "reframe": {
         "hero_sub": ("You don't buy the planet — you subscribe to your acres. AUM pricing "
                      "covers fixed AOIs, so a county, a supply shed, or a project boundary is "
                      "exactly the right size."),
         "compare_row": "Coverage",
     }},
    {"id": "proof_before_buy",
     "text": "We'd need to see it work on our geography first",
     "tracks": ["selfserve", "enterprise"],
     "signals": [("hubspot_abandoned", 14), ("ad_gender", 10), ("ad_broad", 7),
                 ("ad_insurance", 6), ("ad_agriculture", 6), ("tier_1", 6), ("intent_hot", 5)],
     "reframe": {
         "hero_sub": ("You shouldn't take our word for your geography — the archive already "
                      "holds years of it. The 30-day trial opens the sandbox on your own AOI, "
                      "no credit card."),
         "research_body": ("Already started a trial signup? Pick up where you left off — the "
                           "sandbox and 30,000 processing units are waiting."),
         "compare_row": "Next step",
         "final_cta_sub": "Your region is already in the archive — go look.",
     },
     "blocked_say": "You abandoned the trial signup at step 2 of 3 — go back and finish it now"},
    {"id": "free_data_enough",
     "text": "Sentinel and Landsat are free — why pay?",
     "tracks": ["selfserve", "research", "enterprise"],
     "signals": [("audience_route_research", 10), ("audience_route_selfserve", 8),
                 ("ad_docs", 6), ("ad_broad", 6), ("channel_search", 5), ("network_residential", 4)],
     "reframe": {
         "hero_sub": ("Sentinel is 10 m every 5 days; Landsat is 16. PlanetScope is 3 m every "
                      "day — and the Insights Platform hosts the free archives beside it, so "
                      "you keep your workflow and add density."),
         "prove_card": (0, "The free archives are on the platform too — density is the upgrade, "
                        "not the replacement."),
         "compare_row": "Revisit",
     }},
    # --- Research / academic ---
    {"id": "academic_budget",
     "text": "Commercial imagery on a grant budget? Impossible",
     "tracks": ["research"],
     "signals": [("ad_age", 12), ("ad_docs", 10), ("audience_route_research", 10),
                 ("preferential_cost", 6), ("network_residential", 4)],
     "reframe": {
         "hero_sub": ("The Education & Research Program is free for non-commercial work — "
                      "3,000 sq km a month on the Basic tier, used at 1,000+ universities in "
                      "100+ countries."),
         "research_body": ("Apply to the Education & Research Program — free Basic access, "
                           "approval typically inside three weeks, campus licenses for whole "
                           "institutions."),
         "final_cta_sub": "Free for university research. Approval in weeks.",
     }},
    {"id": "licensing_fear",
     "text": "Licensing will block my publication",
     "tracks": ["research"],
     "signals": [("ad_docs", 9), ("audience_route_research", 8), ("technical", 4)],
     "reframe": {
         "hero_sub": ("Publication-grade licensing is the point of the program — roughly two "
                      "papers a day are published on Planet data, thousands to date."),
         "research_body": ("The Education & Research Program ships publication-grade licensing "
                           "by default — cite the data, publish the science."),
     }},
    {"id": "temporal_density",
     "text": "Landsat and Sentinel are fine for my time series",
     "tracks": ["research", "selfserve"],
     "signals": [("ad_age", 9), ("ad_docs", 9), ("audience_route_research", 7),
                 ("channel_search", 4)],
     "reframe": {
         "hero_sub": ("If 16-day revisit hides your signal, the problem isn't your methods — "
                      "it's cadence. Daily 3 m imagery since 2016 turns aliased time series "
                      "into measurements."),
         "prove_card": (2, "A decade of daily observations of your exact study area — no tasked "
                        "or 16-day archive can reconstruct that after the fact."),
         "compare_row": "Revisit",
     }},
    {"id": "switching_effort",
     "text": "Learning a new platform mid-project is a cost",
     "tracks": ["research", "selfserve"],
     "signals": [("audience_route_research", 6), ("audience_route_selfserve", 6),
                 ("ad_broad", 5), ("explorer_archetype", 6)],
     "reframe": {
         "hero_sub": ("The Insights Platform hosts Sentinel and Landsat beside PlanetScope — "
                      "same workflow, same APIs, denser data when you want it. Switching isn't "
                      "a migration; it's a toggle."),
         "compare_row": "Delivery",
     }},
]

OBJECTION_BY_ID = {o["id"]: o for o in OBJECTION_CATALOG}

_SIGNAL_LABELS = {
    "ad_agriculture": "X crop-belt location ad (agriculture)",
    "ad_defense": "X defense lookalike ad (GEOINT)",
    "ad_insurance": "X insurance event ad (claims/cat)",
    "ad_forestry": "X EUDR conversation ad (forest carbon)",
    "ad_energy": "X energy keyword ad (asset integrity)",
    "ad_government": "X civil-gov device ad",
    "ad_maritime": "X maritime interest ad",
    "ad_disaster": "X crisis post-engager retarget",
    "ad_docs": "X Earth-documentary viewer ad",
    "ad_broad": "X broad-reach language ad",
    "ad_age": "X age targeting (25–44, held on page)",
    "ad_gender": "X gender targeting (held on page)",
    "audience_fit_agronomy": "Ad audience fit: VP Digital Ag",
    "audience_fit_geoint": "Ad audience fit: Defense / GEOINT",
    "audience_fit_underwriting": "Ad audience fit: Claims / cat-model",
    "audience_fit_mrv": "Ad audience fit: Forest-carbon MRV",
    "audience_fit_energy": "Ad audience fit: Energy ops",
    "audience_fit_civgov": "Ad audience fit: State agency / GIS",
    "audience_fit_maritime": "Ad audience fit: MDA / enforcement",
    "audience_fit_response": "Ad audience fit: Emergency response",
    "audience_fit_research": "Ad audience fit: University researcher",
    "audience_route_enterprise": "Audience route: enterprise / mission",
    "audience_route_selfserve": "Audience route: self-serve AUM",
    "audience_route_research": "Audience route: education & research",
    "hubspot_abandoned": "HubSpot abandoned trial signup",
    "archetype_cost_confident": "CRM archetype: cost-confident",
    "preferential_cost": "Segment: cost-conscious",
    "seniority_exec": "Clay/LinkedIn: executive",
    "technical": "Clay/LinkedIn: technical profile",
    "network_corporate": "Corporate netblock",
    "network_residential": "Residential / consumer network",
    "industry_resolved": "Reverse-IP industry resolved",
}

_FIT_SIG = {"Agronomy": "audience_fit_agronomy", "GEOINT": "audience_fit_geoint",
            "Underwriting": "audience_fit_underwriting", "Carbon/MRV": "audience_fit_mrv",
            "Energy Ops": "audience_fit_energy", "Civil Gov": "audience_fit_civgov",
            "Maritime": "audience_fit_maritime", "Response": "audience_fit_response",
            "Research": "audience_fit_research"}


def _audience_route(audience: str, ad_variant: dict | None, ident: dict | None) -> str:
    """Narrow audience into enterprise / selfserve / research / neutral for objection routing."""
    if ad_variant:
        route = _AUDIENCE_ROUTE.get(ad_variant["audience_fit"], "neutral")
        if route != "neutral":
            return route
        emph = ad_variant["page"].get("compare_emphasis")
        if emph == "task":
            return "enterprise"
        return "selfserve" if ad_variant["page"].get("cta_primary") == "Start Free Trial" else "neutral"
    if ident and ident.get("kind") == "cohort":
        li = ident["view"]["linkedin"]
        org = (ident["view"]["linkedin"].get("industry") or "").lower()
        if any(w in org for w in ("research", "education", "university", "academ")):
            return "research"
        if li.get("seniority") == "exec" or any(w in org for w in ("defense", "insurance", "maritime", "agri")):
            return "enterprise"
        return "selfserve"
    if audience in ("enterprise", "selfserve", "research"):
        return audience
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
        fit_sig = _FIT_SIG.get(ad_variant["audience_fit"])
        if fit_sig:
            sigs.add(fit_sig)
        if ad_variant["page"].get("compare_emphasis") == "task":
            sigs.add("campaign_tasking")
        elif ad_variant["page"].get("compare_emphasis") == "monitor":
            sigs.add("campaign_monitoring")
    intent = _campaign_intent(entry.get("utm_campaign"))
    if intent:
        sigs.add(f"campaign_{intent}")
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
        elif li.get("seniority") in ("ic", "new_grad"):
            sigs.add("seniority_ic")
        if li.get("technical"):
            sigs.add("technical")
        goal = (dec.get("goal") or "").lower()
        if any(w in goal for w in ("afford", "broke", "cost", "cheap", "budget", "grant")):
            sigs.add("preferential_cost")
        for fam, d in ident["segments"].items():
            for s in d["segments"]:
                if s["id"] == "cost":
                    sigs.add("preferential_cost")
    return sigs


def _objection_applies(obj: dict, route: str) -> bool:
    """Objection must match at least one track for the visitor's route."""
    tracks = obj["tracks"]
    if route in ("enterprise", "selfserve", "research"):
        return route in tracks
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


def _apply_objection_reframes(hero: dict, prove: dict, research: dict, cta: dict,
                              compare_emphasis: str | None, prove_cards: list,
                              prioritized: list[dict], *, preserve_hero_sub: bool = False
                              ) -> tuple[dict, dict, dict, dict, str | None, list,
                                         str | None, list[dict]]:
    """Weave prioritized objections into copy slots. Returns updated sections + slot assignments."""
    assignments: list[dict] = []
    row_emphasis: str | None = None
    if not prioritized:
        return hero, prove, research, cta, compare_emphasis, prove_cards, row_emphasis, assignments

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

    # #3 → prove card or compare / research callout
    if len(prioritized) > 2:
        o3 = prioritized[2]["objection"]
        rf3 = o3.get("reframe", {})
        if rf3.get("research_body"):
            research["body"] = rf3["research_body"]
            assignments.append({"rank": 3, "objection_id": o3["id"], "objection": o3["text"],
                                "slot": "research_body", "policy": "allude"})
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

    # #1 may also set compare row / emphasis / research body if not consumed
    if rf1.get("compare_row") and not row_emphasis:
        row_emphasis = rf1["compare_row"]
        assignments.append({"rank": 1, "objection_id": o1["id"], "objection": o1["text"],
                            "slot": "compare_row", "policy": "allude"})
    if rf1.get("compare_emphasis"):
        compare_emphasis = rf1["compare_emphasis"]
    if rf1.get("research_body"):
        research["body"] = rf1["research_body"]
        assignments.append({"rank": 1, "objection_id": o1["id"], "objection": o1["text"],
                            "slot": "research_body", "policy": "allude"})

    # Final CTA — last prioritized objection with final_cta_sub
    for row in reversed(prioritized):
        rf = row["objection"].get("reframe", {})
        if rf.get("final_cta_sub"):
            cta["sub"] = rf["final_cta_sub"]
            assignments.append({"rank": row["rank"], "objection_id": row["objection_id"],
                                "objection": row["text"], "slot": "final_cta", "policy": "allude"})
            break

    return hero, prove, research, cta, compare_emphasis, prove_cards, row_emphasis, assignments


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
    """Who the visitor is, if anyone: login email (say) or the email magic token (say).
    Cohort hit → the full CRM record; unknown work email → first-party domain resolution."""
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
    """Route the page to an audience: enterprise (direct sales / satellite services),
    selfserve (AUM + trial), research (Education & Research Program), or neutral.
    Returns (audience, rule, why)."""
    if variant:
        aud = variant["audience"]
        return (aud,
                f"ad variant {variant['id']} (utm_campaign={variant['utm_campaign']})",
                f"the X.com ad used {variant['x_targeting_type']} targeting "
                f"({variant['x_targeting_example']}) — message-match the hero to that promise")
    intent = _campaign_intent(entry.get("utm_campaign"))
    if intent:
        return intent, f"utm_campaign={entry['utm_campaign']} message-matches {intent}", \
            "the campaign promise decides the emphasis — mission campaigns lead with " \
            "enterprise sales, trial campaigns with self-serve, academic campaigns with research"
    if ident and ident["kind"] == "cohort":
        li = ident["view"]["linkedin"]
        ind = (li.get("industry") or "").lower()
        if any(w in ind for w in ("research", "education", "university", "academ")):
            return "research", f"CRM: industry={li.get('industry')}", \
                "the CRM record describes a researcher — Education & Research framing"
        if li.get("seniority") == "exec":
            return "enterprise", f"CRM: seniority={li.get('seniority')}", \
                "a senior leader buys programs, not subscriptions — enterprise framing"
        return "selfserve", f"CRM: seniority={li.get('seniority')} — an operating team", \
            "the CRM record describes a practitioner — self-serve AUM framing"
    if ident and ident["kind"] == "resolved" and ident["resolved"].get("company"):
        return "enterprise", f"work-email domain → {ident['resolved']['company']}", \
            "a work email identifies a company — enterprise framing"
    net = det.get("network_type", "")
    if net in ("corporate", "corporate (via VPN)"):
        return "enterprise", f"network type = {net}", \
            "a corporate netblock is a B2B signal — emphasize enterprise sales"
    if net in ("residential", "consumer ISP", "mobile"):
        return "selfserve", f"network type = {net}", \
            "a residential/mobile visitor is likelier a practitioner or researcher — " \
            "emphasize the self-serve trial"
    return "neutral", f"network type = {net or 'unknown'} — no audience signal", \
        "VPN/hosting/unknown networks say nothing about who's visiting — the real-site default ships"


def _ind_label(det: dict) -> str:
    key = det.get("industry")
    return SC.BY_KEY[key]["label"].lower() if key else ""


def build_page(request, email: str | None = None, overrides: dict | None = None) -> dict:
    """Compose entry channel × IP tier × location × identity/CRM into the replica's page
    contract + the full decision trace. Deterministic: same inputs → same page, same trace."""
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
            f"segment={ad_variant['segment']}",
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

    # --- LOCATION — the Planet differentiator, a first-class decision stage ------
    loc = location_signal(det, tier, ad_variant)
    loc_sigs = [f"region={loc['region'] or region or '—'}", f"tier={tier}",
                f"segment={loc['segment'] or '—'}", f"mode={loc['mode']}"]
    t("Location signal", loc_sigs, loc["rule"], loc["policy"],
      (f"“{loc['line']}”" if loc["line"] else "no location claim"),
      loc["why"])

    if ident and ident["kind"] == "cohort":
        v = ident["view"]
        t("Identity", [f"{ident['via']} → {ident['email']}"],
          "planet_cohort.match(email)" if ident["via"] == "login" else "planet_cohort.by_token(e)",
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
        t("Identity", ["(no login, no token)"], "planet_cohort.match / by_token", "hold",
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
    research = dict(GENERIC["research"])
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
        eyebrow = f"For {industry} teams" + (f" in {region}" if region else "")
        eyebrow_src, eyebrow_pol = "reverse-IP firmographic (allude — shapes, never recites)", "allude"
        blocked_eyebrow = f"{company} — we see your {industry} operation in {city or region}"
    elif tier == 1 and region:
        eyebrow = f"Planet imaged {region} today"
        eyebrow_src, eyebrow_pol = "geo-IP region (allude) — the daily-coverage claim", "allude"
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

    # --- hero location line: THE Planet signal -------------------------------
    hero["location_line"] = slot(
        "hero_location", "Hero location line", "", loc["line"],
        ("defense theater register (guardrail)" if loc["mode"] == "theater"
         else "geo-IP region × segment template (allude)" if loc["mode"] == "region"
         else "no location confidence"),
        loc["policy"],
        blocked_say=loc["blocked_say"],
        why="Planet images every place on Earth daily — the region claim is literally true, "
            "so it ships at region scale; street/property scale and defense self-location are held")

    # --- hero headline + sub: message-match to the campaign / archetype -----
    h1_pre, h1_blue, sub = hero["h1_pre"], hero["h1_blue"], hero["sub"]
    h_src, h_pol = "—", "say"
    if ad_variant:
        vp = ad_variant["page"]
        h1_pre, h1_blue, sub = vp["h1_pre"], vp["h1_blue"], vp["sub"]
        h_src = f"ad variant {ad_variant['id']} (utm_campaign={ad_variant['utm_campaign']})"
        h_pol = "allude"
    elif entry["channel"] == "ad" and _campaign_intent(entry["utm_campaign"]) == "enterprise":
        h1_pre, h1_blue = "Broad Area Management at ", "Mission Scale"
        sub = ("Daily coverage of the entire landmass plus dedicated tasking capacity — "
               "sovereign-grade Earth intelligence without building a constellation.")
        h_src, h_pol = f"ad message-match (utm_campaign={entry['utm_campaign']})", "allude"
    elif entry["channel"] == "ad" and _campaign_intent(entry["utm_campaign"]) == "selfserve":
        h1_pre, h1_blue = "Your AOI, ", "Every Day"
        sub = ("Self-serve Area Under Management puts daily 3 m imagery over exactly the acres "
               "you manage — start with a 30-day free trial, no credit card.")
        h_src, h_pol = f"ad message-match (utm_campaign={entry['utm_campaign']})", "allude"
    elif entry["channel"] == "ad" and _campaign_intent(entry["utm_campaign"]) == "research":
        h1_pre, h1_blue = "Daily Earth Data for ", "Science"
        sub = ("The Education & Research Program puts daily 3 m imagery behind your research — "
               "free for non-commercial university work, publication-grade licensing.")
        h_src, h_pol = f"ad message-match (utm_campaign={entry['utm_campaign']})", "allude"
    elif ident and ident["kind"] == "cohort":
        goal = ident["view"]["declared"].get("goal", "")
        if goal:
            sub = f"You told us you want to {goal} — the constellation is already overhead."
            h_src, h_pol = "HubSpot form · interest reason (declared → say)", "say"
        else:
            arch = ident["archetype"]
            sub = f"Tuned for {arch['for']} — " + hero["sub"][0].lower() + hero["sub"][1:]
            h_src, h_pol = f"archetype {arch['label']} (modeled → allude)", "allude"
    hero["h1_pre"], hero["h1_blue"] = h1_pre, h1_blue
    hero["sub"] = slot("hero_sub", "Hero headline + sub", GENERIC["hero"]["sub"], sub, h_src, h_pol,
                       blocked_say=(f"Your modeled income is {ident['view']['deep']['income_band']} — "
                                    "we pre-picked a subscription tier"
                                    if ident and ident["kind"] == "cohort"
                                    and ident["view"]["deep"].get("income_band") else None),
                       why="ad clicks message-match the campaign promise; a declared goal may be "
                           "recited verbatim (say); modeled income is hold — never shipped")
    diff[-1]["generic"] = GENERIC["hero"]["h1_pre"] + GENERIC["hero"]["h1_blue"] + " · " + GENERIC["hero"]["sub"]
    diff[-1]["shipped"] = h1_pre + h1_blue + " · " + sub
    diff[-1]["changed"] = diff[-1]["generic"] != diff[-1]["shipped"]

    # --- hero CTAs: primary/secondary order follows the audience ------------
    ctas = {"enterprise": ("Talk to Sales", "Start Free Trial"),
            "selfserve": ("Start Free Trial", "Talk to Sales"),
            "research": ("Apply for Research Access →", "Start Free Trial"),
            "neutral": ("Talk to Sales", "Start Free Trial")}[audience]
    if ad_variant:
        vp = ad_variant["page"]
        ctas = (vp["cta_primary"], vp["cta_secondary"])
    if ident and ident["kind"] == "cohort":
        ctas = (ident["archetype"]["cta"], ctas[0] if ctas[0] != ident["archetype"]["cta"] else ctas[1])
    hero["cta_primary"], hero["cta_secondary"] = ctas
    slot("hero_cta", "Hero CTAs",
         GENERIC["hero"]["cta_primary"] + " / " + GENERIC["hero"]["cta_secondary"],
         ctas[0] + " / " + ctas[1],
         ("archetype CTA (CRM)" if ident and ident["kind"] == "cohort" else f"audience = {audience}"),
         "allude", why="emphasis only — both paths stay on the page")

    # --- prove intro: firmographic + location allusion -----------------------
    intro = prove["intro"]
    p_src, p_pol = "—", "say"
    if ad_variant and ad_variant["page"].get("prove_intro"):
        intro = ad_variant["page"]["prove_intro"]
        p_src = f"ad variant {ad_variant['id']} message-match"
        p_pol = "allude"
    elif tier >= 2 and industry:
        intro = (f"Daily monitoring built for {industry} operations — the entire landmass every "
                 "day, tasking on demand, and analysis-ready feeds that land in your stack.")
        p_src, p_pol = "reverse-IP industry (allude)", "allude"
    elif loc["mode"] == "region" and loc["region"]:
        intro = (GENERIC["prove"]["intro"] + f" {loc['region']} included — today, and every "
                 "day back to 2016.")
        p_src, p_pol = "geo-IP region (allude) — the archive claim", "allude"
    elif ident and ident["kind"] == "cohort" and ident["view"]["linkedin"].get("technical"):
        intro = (GENERIC["prove"]["intro"] + " You work in the data — this is how it gets to you.")
        p_src, p_pol = "Clay technical flag (enriched → allude)", "allude"
    prove["intro"] = slot("prove_intro", "\u201cHow we prove\u201d intro", GENERIC["prove"]["intro"], intro,
                          p_src, p_pol,
                          blocked_say=(f"{company}'s assets could use this" if company else None),
                          why="industry and region may shape the frame (allude); the company name "
                              "may not be recited")

    # --- research callout: emphasis + warm body -------------------------------
    rs_body = research["body"]
    rs_src, rs_pol = "—", "say"
    if ad_variant and ad_variant["page"].get("research_body"):
        rs_body = ad_variant["page"]["research_body"]
        rs_src = f"ad variant {ad_variant['id']} message-match"
        rs_pol = "allude"
    elif ident and ident["kind"] == "cohort" and ident["archetype"]["id"] in ("cost_confident", "outcomes_first", "fast_track"):
        arch = ident["archetype"]
        rs_body = (GENERIC["research"]["body"] + f" Built for {arch['for']}.")
        rs_src, rs_pol = f"archetype {arch['label']} (modeled → allude)", "allude"
    research["body"] = slot("research_body", "Research callout", GENERIC["research"]["body"],
                            rs_body, rs_src, rs_pol,
                            why="the archetype may add a framing line; the segment itself is never named")
    research["emphasis"] = (
        ad_variant["page"].get("research_hot", False) if ad_variant
        else audience == "research"
    )

    # --- comparison table: column emphasis follows the audience -------------
    compare_emphasis = {"enterprise": "task", "selfserve": "monitor",
                        "research": "monitor", "neutral": None}[audience]
    if ad_variant:
        compare_emphasis = ad_variant["page"]["compare_emphasis"]
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
            "Your workspace is saved — the next pass is already overhead."
        f_src, f_pol = "HubSpot past-customer (first-party → allude)", "allude"
    elif ident and ident["kind"] == "cohort" and ident["view"]["hubspot"].get("abandoned"):
        f_head, f_sub = "Finish what you started", \
            "Your trial is most of the way set up — the sandbox is waiting."
        f_src, f_pol = "HubSpot abandoned action (behavioral → allude)", "allude"
    elif loc["mode"] == "region" and loc["region"]:
        f_sub = f"{loc['region']} is already in today's take. Go look."
        f_src, f_pol = "geo-IP region (allude) — location close", "allude"
    cta["heading"], cta["sub"] = f_head, f_sub
    slot("final_cta", "Final CTA block", GENERIC["cta"]["heading"] + " · " + GENERIC["cta"]["sub"],
         f_head + " · " + f_sub, f_src, f_pol,
         blocked_say=(f"You bailed at the {ident['view']['hubspot']['abandoned']} on "
                      f"{ident['view']['hubspot']['visits']} visits — go back"
                      if ident and ident["kind"] == "cohort" and ident["view"]["hubspot"].get("abandoned") else None),
         why="behavioral facts steer the close but are alluded to, never itemized")

    # --- objection-driven reframes (deterministic checklist → copy slots) ---
    prove_cards = [tuple(cd) for cd in PROVE_CARDS]
    pre_hero_sub = hero["sub"]
    pre_research_body = research["body"]
    pre_cta_sub = cta["sub"]
    pre_compare_emphasis = compare_emphasis

    aud_route = _audience_route(audience, ad_variant, ident)
    obj_ctx = {"entry": entry, "ad_variant": ad_variant, "audience": audience,
               "tier": tier, "ident": ident, "det": det, "route": aud_route}
    prioritized = prioritize_objections(obj_ctx)
    hero_sub_say = bool(ident and ident["kind"] == "cohort"
                        and ident["view"]["declared"].get("goal"))
    hero, prove, research, cta, compare_emphasis, prove_cards, compare_row_emphasis, obj_assignments = \
        _apply_objection_reframes(hero, prove, research, cta, compare_emphasis, prove_cards, prioritized,
                                  preserve_hero_sub=hero_sub_say)

    obj_blocked = [{"objection_id": row["objection"]["id"], "text": row["objection"]["text"],
                    "blocked_say": row["objection"].get("blocked_say")}
                   for row in prioritized if row["objection"].get("blocked_say")]

    if hero["sub"] != pre_hero_sub:
        for d in diff:
            if d["slot"] == "hero_sub":
                d["shipped"] = h1_pre + h1_blue + " · " + hero["sub"]
                d["changed"] = d["generic"] != d["shipped"]
                d["source"] = d["source"] + " + objection #" + str(prioritized[0]["rank"])
                d["why"] = (d.get("why", "") + " · objection #" + str(prioritized[0]["rank"])
                            + " reframe woven into hero sub")
                break
    if research["body"] != pre_research_body:
        for d in diff:
            if d["slot"] == "research_body":
                d["shipped"] = research["body"]
                d["changed"] = True
                d["source"] = "objection-driven reframe"
                break
        else:
            slot("research_body", "Research callout", GENERIC["research"]["body"],
                 research["body"], "objection-driven reframe", "allude",
                 why="prioritized research-track objection addressed in callout")
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
      "score OBJECTION_CATALOG signals → rank top 3–5 → weave into hero/prove/compare/research/CTA",
      "allude",
      f"{len(prioritized)} objections ranked" if prioritized else "no objections matched",
      "sales psychology meets them where they are — every reframe uses only verified Planet "
      "claims; blocked say-level variants appear on /planet/dev for contrast")

    order = (ad_variant["page"].get("order") if ad_variant and ad_variant["page"].get("order")
             else ORDER_BY_AUDIENCE[audience])
    t("Surface policy", [f"{d['slot']}: {d['policy']}" for d in diff],
      "say = recite · allude = shape only · hold = never ships (docs/04-workflow)",
      "mixed", f"{sum(1 for d in diff if d['changed'])} of {len(diff)} slots personalized",
      "every personalized slot carries its source + policy; the say-level recite variants are "
      "blocked and appear only on /planet/dev")
    t("Compose", [f"order = {' → '.join(order)}"],
      f"section order for audience = {audience}", "allude",
      "same sections, same facts — only emphasis and order move",
      "the structure is identical before and after login; personalization never adds or removes a claim")

    hero_image = IG.resolve_hero_image({
        "entry": entry, "det": det, "identity": ident, "ad_variant": ad_variant,
        "audience": audience, "audience_route": aud_route, "tier": tier,
        "objections": {"prioritized": prioritized},
        "sections": {"hero": hero, "compare": {"emphasis": compare_emphasis}},
    }, generate=False, tenant=IMAGE_TENANT)
    img_receipt = hero_image.get("receipt") or {}
    img_sigs, img_out, img_why = IG.hero_image_trace(img_receipt)
    t("Hero image resolve", img_sigs,
      "disk cache → (async API if keyed) → scene.image_for gallery → CSS gradient",
      "say", img_out, img_why)
    motion_receipt = hero_image.get("motion_receipt") or {}
    if MG.motion_enabled(tenant=IMAGE_TENANT):
        m_sigs, m_out, m_why = MG.hero_motion_trace(motion_receipt)
        t("Hero motion resolve", m_sigs,
          "keyframe stills → animated WebP loop (simulated change-over-time)",
          "say", m_out, m_why)
    brain = brain_sim_signal(img_receipt)
    if brain["enabled"]:
        bs_sigs = [f"intent={brain.get('intent_id') or '—'}",
                   f"brain_target={brain.get('brain_target') or '—'}"]
        if brain.get("brain_score") is not None:
            bs_sigs.append(f"brain_score={brain['brain_score']}")
            bs_sigs.append(f"simulator={brain.get('brain_simulator') or 'proxy_v1'}")
        if brain.get("candidates_evaluated"):
            bs_sigs.append(f"candidates={brain['candidates_evaluated']}")
        t("Brain simulator", bs_sigs, brain["rule"], brain["policy"],
          brain["output"], brain["why"])

    ledger = _ledger(entry, det, ident, loc)
    ledger.extend(IG.hero_image_ledger_rows(img_receipt))
    ledger.extend(MG.hero_motion_ledger_rows(motion_receipt))
    login_state = bool(ident and ident.get("via") == "login")
    return {
        "entry": entry, "det": det, "ip_forced": ip_forced, "identity": ident,
        "audience": audience, "audience_rule": aud_rule,
        "tier": tier, "tier_label": tier_label, "confidence": conf,
        "location": loc,
        "sections": {"hero": hero, "prove": {**prove, "cards": prove_cards},
                     "research": research,
                     "compare": {"rows": COMPARE_ROWS, "emphasis": compare_emphasis,
                                 "row_emphasis": compare_row_emphasis},
                     "numbers": {"stats": stats, "trusted": TRUSTED_BY},
                     "cta": cta},
        "order": order,
        "nav": {"login_state": login_state,
                "login_email": ident["email"] if ident else "",
                "first": ident["first"] if ident and ident.get("first") else "",
                "known": bool(ident),
                "ads": None, "ads_lp": None},
        "login_state": login_state,
        "ad_variant": ad_variant,
        "audience_route": aud_route,
        "objections": {"prioritized": prioritized, "assignments": obj_assignments,
                       "blocked": obj_blocked},
        "trace": trace, "copy_diff": diff, "ledger": ledger,
        "hero_image": hero_image,
        "brain_sim": brain,
    }


# --------------------------------------------------------------------------- #
# Signal ledger for /planet/dev — source · vendor · tier · disposition
# --------------------------------------------------------------------------- #
_DISPOSITION = {"say": "said", "allude": "steer", "hold": "held", "observed": "observed"}


def _ledger(entry: dict, det: dict, ident: dict | None, loc: dict | None = None) -> list[dict]:
    rows: list[dict] = []

    def add(label, value, source, vendor, policy):
        rows.append({"label": label, "value": value if value not in (None, "") else "—",
                     "source": source, "vendor": vendor, "policy": policy,
                     "disposition": _DISPOSITION.get(policy, policy)})

    add("Entry channel", entry["channel_label"], "observed", "UTM / Referer parse", "observed")
    for s in entry["signals"]:
        if s["value"] != "—":
            add(s["label"], s["value"], "observed", "query string / Referer header", "allude")
    for cc in det.get("captured", []):
        add(cc["label"], cc["value"], "observed", "ip-api.com" + (" → PDL" if cc["group"] == "resolved" else ""),
            cc["policy"])
    for cc in det.get("request_signals", []):
        add(cc["label"], cc["value"], "observed", "HTTP headers", cc["policy"])
    if loc and loc.get("line"):
        add("Location line", loc["line"], "derived", "geo-IP region × segment template", "allude")
    if loc and loc.get("blocked_say"):
        add("Location recite (blocked)", loc["blocked_say"], "derived",
            "geo-IP city precision — anti-surveillance guardrail", "hold")
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
        for cc in ident["resolved"].get("captured", []):
            add(cc["label"], cc["value"], "declared", "work-email domain → PDL", cc["policy"])
    return rows


# --------------------------------------------------------------------------- #
# Process map for /planet/dev — the pipeline as a diagram: every decision, every
# branch, every piece of data each stage reads. Pure function of the built page
# dict, so the diagram can never drift from what actually ran.
# --------------------------------------------------------------------------- #
NETWORK_BRANCHES = ["corporate", "corporate (via VPN)", "consumer ISP", "residential",
                    "mobile", "VPN / proxy", "hosting / cloud", "private / unreachable"]
ROUTE_LABELS = {"enterprise": "enterprise", "selfserve": "self-serve",
                "research": "research", "neutral": "neutral"}


def _branches(options: list[str], taken: str | None) -> list[dict]:
    return [{"label": o, "taken": o == taken} for o in options]


def _kv(k: str, v, pol: str | None = None, fired: bool = False) -> dict:
    """One drill-down row: label → value, optional policy tag, optional 'fired' marker."""
    return {"k": k, "v": v if v not in (None, "") else "—", "pol": pol, "fired": fired}


def process_map(page: dict) -> dict:
    """The /planet/dev process diagram: {inputs, stages}. Thirteen stages — the Gauntlet
    eleven plus Location signal and Brain simulator (Planet image decisioning). Skipped stages
    stay visible, marked skipped — the full decision space is always on screen."""
    P = page
    entry, det, ident, ad = P["entry"], P["det"], P["identity"], P.get("ad_variant")
    loc = P.get("location") or {}
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
         "feeds": "IP resolve · tier route · location signal"},
        {"label": "Login cookie / magic token",
         "value": (ident["email"] + f" (via {ident['via']})") if ident else "(none — anonymous)",
         "feeds": "identity · CRM · segments"},
    ]

    stages: list[dict] = []

    def stage(id_, title, link, reads, rule, branches, output, why,
              skipped=False, skip_reason="", detail=None):
        stages.append({"id": id_, "title": title, "link": link, "reads": reads,
                       "rule": rule, "branches": branches, "output": output, "why": why,
                       "skipped": skipped, "skip_reason": skip_reason,
                       "detail": detail or []})

    # 1 · entry channel
    entry_detail = [_kv(s["label"], s["value"]) for s in entry["signals"]]
    entry_detail += [
        _kv("rule · ad", "utm_medium ∈ {paid, cpc, ppc, display}", fired=entry["channel"] == "ad"),
        _kv("rule · email", "utm_medium=email (+ optional e= magic token)", fired=entry["channel"] == "email"),
        _kv("rule · search", "?ref ∈ {google, bing, ddg} or a search-engine Referer", fired=entry["channel"] == "search"),
        _kv("rule · direct", "nothing matched — the click says nothing", fired=entry["channel"] == "direct"),
    ]
    stage("entry", "Entry classify", "#sec-entry",
          [f"utm_medium={sig.get('utm_medium', '—')}", f"utm_campaign={sig.get('utm_campaign', '—')}",
           f"ref={sig.get('ref', '—')}", f"Referer={'search engine' if entry['channel'] == 'search' and not entry['ref'] else (entry['referer'] and 'set') or '—'}",
           f"e token={'present' if entry['token'] else '—'}"],
          entry["rule"],
          _branches(["ad", "email", "search", "direct"], entry["channel"]),
          f"channel = {entry['channel_label']}", entry["why"],
          detail=entry_detail)

    # 2 · ad variant (only meaningful on a paid click)
    is_ad = entry["channel"] == "ad"
    intent = _campaign_intent(entry.get("utm_campaign"))
    ad_taken = ("catalogued variant" if ad else
                ("campaign keyword intent" if intent else "no match") if is_ad else None)
    if ad:
        vp = ad["page"]
        overridden = [k for k in ("hero_eyebrow", "h1_pre", "sub", "cta_primary", "cta_secondary",
                                  "compare_emphasis", "order", "prove_intro", "research_body",
                                  "cta_heading", "stat_highlight") if vp.get(k) not in (None, "", False)]
        ad_detail = [
            _kv("Variant", f"{ad['id']} ({ad['variant_id']}) · campaign {ad['utm_campaign']}"),
            _kv("Segment", ad["segment"]),
            _kv("X targeting", f"{ad['x_targeting_type']} — {ad['x_targeting_example']}"),
            _kv("Audience fit", f"{ad['audience_fit_label']} → route {ad['audience']}"),
            _kv("Ad · trigger", ad["ad"]["trigger"]),
            _kv("Ad · body", ad["ad"]["body"]),
            _kv("Ad · proof", ad["ad"]["proof"]),
            _kv("Slots overridden", ", ".join(overridden)),
        ]
        if ad.get("hold_note"):
            ad_detail.append(_kv("Hold note", ad["hold_note"], pol="hold"))
    else:
        ad_detail = [
            _kv("Catalog", f"{len(AD_VARIANTS)} X.com variants across {len(AD_CATEGORIES)} targeting categories"),
            _kv("Lookup order", "utm_content (v01–v12) first, then utm_campaign"),
            _kv("Keyword fallback", "campaign name keywords → enterprise / selfserve / research intent"),
        ]
        if is_ad and intent:
            ad_detail.append(_kv("Matched intent", f"utm_campaign={entry['utm_campaign']} → {intent}", fired=True))
    stage("advariant", "Ad variant resolve", "#sec-entry",
          [f"utm_campaign={sig.get('utm_campaign', '—')}", f"utm_content={sig.get('utm_content', '—')}"],
          "AD_BY_VARIANT_ID / AD_BY_CAMPAIGN lookup, else keyword intent",
          _branches(["catalogued variant", "campaign keyword intent", "no match"], ad_taken),
          (f"{ad['id']} · {ad['x_targeting_type']}" if ad
           else (f"intent = {intent}" if is_ad and intent else "generic ad framing" if is_ad else "—")),
          "a catalogued X variant message-matches every copy slot to the ad promise",
          skipped=not is_ad, skip_reason="not a paid click — no ad promise to match",
          detail=ad_detail)

    # 3 · IP resolve → network type
    firmo = " · ".join(x for x in (
        f"company={det.get('company')}" if det.get("company") else "",
        f"region={det.get('region')}" if det.get("region") else "",
        f"industry={_ind_label(det)}" if _ind_label(det) else "") if x) or "no firmographics"
    ip_detail = ([_kv(cc["label"], f"{cc['value']} → drives {cc['drives']}", pol=cc.get("policy"))
                  for cc in det.get("captured", [])]
                 or [_kv("Captured", "nothing — private / unreachable IP resolves no signals")])
    ip_detail += [_kv(cc["label"], cc["value"], pol=cc.get("policy"))
                  for cc in det.get("request_signals", [])]
    if det.get("reason"):
        ip_detail.append(_kv("Router reason", det["reason"]))
    stage("ip", "IP resolve + classify", "#sec-tier",
          [f"ip={det.get('ip') or '—'}" + (" (?ip= override)" if P.get("ip_forced") else ""),
           f"isp={det.get('isp') or '—'}"],
          "reverse-IP (ip-api) → network flags → deterministic router (scene._classify)",
          _branches(NETWORK_BRANCHES, det.get("network_type") or "private / unreachable"),
          firmo, det.get("reason") or "network flags decide how much the IP is allowed to imply",
          detail=ip_detail)

    # 4 · tier route
    conf = P["confidence"]
    tier_detail = [
        _kv("Confidence · location", conf["location"]),
        _kv("Confidence · company", conf["company"]),
        _kv("Confidence · industry", conf["industry"]),
        _kv("tier 0 · neutral", "nothing usable — real-site default ships", fired=P["tier"] == 0),
        _kv("tier 1 · location-aware", "geo confidence high/medium, not hosting/VPN", fired=P["tier"] == 1),
        _kv("tier 2 · firmographic", "company + industry resolved", fired=P["tier"] == 2),
        _kv("tier 3 · firmographic + competitive", "tier 2 + competitive angle engaged", fired=P["tier"] == 3),
        _kv("Competitive eligible", "yes" if det.get("competitive_eligible") else "no"),
    ]
    stage("tier", "Tier route", "#sec-tier",
          [f"confidence: location={conf['location']} · company={conf['company']} · industry={conf['industry']}"],
          "industry resolved → 2 · geo only → 1 · nothing usable → 0",
          _branches([f"{k} · {v}" for k, v in SC.TIER_LABELS.items()],
                    f"{P['tier']} · {P['tier_label']}"),
          f"tier {P['tier']} · {P['tier_label']}",
          "the tier gates which copy path runs — never what we recite",
          detail=tier_detail)

    # 5 · LOCATION SIGNAL — Planet's first-class decision
    loc_taken = {"region": "region line (allude)", "theater": "theater register (defense)",
                 "none": "no claim (tier 0)"}.get(loc.get("mode", "none"))
    loc_detail = [
        _kv("Region (geo-IP)", loc.get("region") or det.get("region") or "—", pol="allude"),
        _kv("Segment", loc.get("segment") or "— (no ad segment — default line)"),
    ]
    for seg_key, template in LOCATION_LINES.items():
        loc_detail.append(_kv(f"template · {seg_key}", template,
                              fired=loc.get("mode") == "region" and loc.get("segment") == seg_key))
    loc_detail.append(_kv("template · default", DEFAULT_LOCATION_LINE,
                          fired=loc.get("mode") == "region"
                          and loc.get("segment") not in LOCATION_LINES))
    loc_detail.append(_kv("template · defense theater", THEATER_LINE,
                          fired=loc.get("mode") == "theater"))
    if loc.get("blocked_say"):
        loc_detail.append(_kv("Blocked recite (street/property scale)", f"\u201c{loc['blocked_say']}\u201d",
                              pol="hold"))
    loc_detail.append(_kv("Guardrail", "region/landscape scale only — never street or property "
                                       "scale; defense gets theater-of-interest, never own location",
                          pol="hold"))
    stage("location", "Location signal", "#sec-location",
          [f"region={loc.get('region') or det.get('region') or '—'}",
           f"tier={P['tier']}", f"segment={loc.get('segment') or '—'}"],
          loc.get("rule", "tier ≥ 1 + region → segment template; defense → theater register"),
          _branches(["region line (allude)", "theater register (defense)", "no claim (tier 0)"],
                    loc_taken),
          (f"\u201c{loc['line']}\u201d" if loc.get("line") else "no location claim ships"),
          loc.get("why", "Planet images every place on Earth daily — the region claim is truthful"),
          detail=loc_detail)

    # 6 · identity
    id_taken = ("cohort CRM" if ident and ident["kind"] == "cohort"
                else "work-email resolved" if ident and ident["kind"] == "resolved"
                else "anonymous")
    if ident and ident["kind"] == "cohort":
        v = ident["view"]
        id_detail = [
            _kv("Identified via", f"{ident['via']} → {ident['email']}", pol="say"),
            _kv("Name", v["name"], pol="say"),
            _kv("Vector — de-anon", f"{v['linkedin']['title']} · {v['linkedin']['company']} · {v['linkedin']['location']}", pol="allude"),
            _kv("HubSpot — behavior", f"{v['hubspot']['lifecycle']} · score {v['hubspot']['lead_score']} · {v['hubspot']['visits']} visits · pages {', '.join(v['hubspot']['top_pages'])}", pol="allude"),
            _kv("Clay — enrichment", f"{v['linkedin']['seniority']} · {v['linkedin']['tenure']}y · {v['linkedin']['industry']}", pol="allude"),
        ]
        if v["declared"].get("goal"):
            id_detail.append(_kv("Declared goal", f"\u201c{v['declared']['goal']}\u201d", pol="say"))
        if v["hubspot"].get("abandoned"):
            id_detail.append(_kv("Abandoned action", v["hubspot"]["abandoned"], pol="allude"))
        if v["deep"].get("income_band"):
            id_detail.append(_kv("Modeled income", v["deep"]["income_band"], pol="hold"))
    elif ident and ident["kind"] == "resolved":
        r = ident["resolved"]
        id_detail = [
            _kv("Identified via", f"login → {ident['email']}", pol="say"),
            _kv("Domain → company", f"{r.get('company') or '—'} · tier {r.get('tier', 0)} ({r.get('tier_label', '—')})"),
        ]
        if r.get("reason"):
            id_detail.append(_kv("Why", r["reason"]))
    else:
        id_detail = [
            _kv("Cookie", "not set — no login this session"),
            _kv("Magic token", "absent — not an identified email click"),
            _kv("What would unlock", f"log in as {sample_login_email()} (cohort CRM) or any work email (domain resolution)"),
        ]
    stage("identity", "Identity", "#sec-crm",
          [f"cookie={'set' if ident and ident.get('via') == 'login' else '—'}",
           f"magic token={'present' if entry['token'] else '—'}"],
          "planet_cohort.match(email) / by_token(e), else resolve_email() first-party domain",
          _branches(["cohort CRM", "work-email resolved", "anonymous"], id_taken),
          (f"{ident['email']} via {ident['via']}" if ident else "anonymous"),
          ("they identified themselves — say-level facts unlock; enrichment stays allude/hold"
           if ident else "no identity offered — nothing personal may be said"),
          detail=id_detail)

    # 7 · segments → archetype (cohort only)
    is_cohort = bool(ident and ident["kind"] == "cohort")
    if is_cohort:
        arch = ident["archetype"]
        arch_detail = [_kv(f"{d['label']} ({d['source']})",
                           "; ".join(f"{s['label']} — {', '.join(s['evidence'])}" for s in d["segments"]) or "—",
                           pol="allude")
                       for fam, d in ident["segments"].items()]
        arch_detail += [
            _kv("Archetype picked", f"{arch['label']} — {arch['reason']}", fired=True),
            _kv("Drives", f"sections {' → '.join(arch['sections'])} · CTA \u201c{arch['cta']}\u201d"),
        ]
    else:
        arch_detail = [_kv(a["label"], f"for {a['for']} — CTA \u201c{a['cta']}\u201d")
                       for a in SEG.ARCHETYPES.values()]
    stage("archetype", "Segments → archetype", "#sec-crm",
          ([f"{fam}: " + ", ".join(s["label"] for s in d["segments"])
            for fam, d in ident["segments"].items()] if is_cohort else ["(no CRM record)"]),
          "segments.derive() → pick_archetype()",
          _branches([a["label"] for a in SEG.ARCHETYPES.values()],
                    ident["archetype"]["label"] if is_cohort else None),
          (f"archetype = {ident['archetype']['label']}" if is_cohort else "—"),
          ("behavioral + enriched segments choose emphasis and section order — never recited"
           if is_cohort else ""),
          skipped=not is_cohort, skip_reason="no CRM record — no segments to derive",
          detail=arch_detail)

    # 8 · audience route — the precedence chain, each rung with its evidence
    fired_rung = ("ad variant" if ad else
                  "campaign intent" if intent else
                  "CRM record" if is_cohort else
                  "work-email domain" if ident and ident["kind"] == "resolved" and ident["resolved"].get("company") else
                  "network type")
    aud_detail = [
        _kv("1 · ad variant", f"{ad['id']} → {ad['audience']}" if ad else "no catalogued ad variant",
            fired=fired_rung == "ad variant"),
        _kv("2 · campaign intent", f"utm_campaign={entry['utm_campaign']} → {intent}" if intent
            else "no campaign keyword match", fired=fired_rung == "campaign intent"),
        _kv("3 · CRM record",
            (f"seniority={ident['view']['linkedin'].get('seniority')} · industry \u201c{ident['view']['linkedin'].get('industry') or '—'}\u201d"
             if is_cohort else "no CRM record"), fired=fired_rung == "CRM record"),
        _kv("4 · work-email domain",
            (f"→ {ident['resolved']['company']}" if ident and ident["kind"] == "resolved"
             and ident["resolved"].get("company") else "no resolved work email"),
            fired=fired_rung == "work-email domain"),
        _kv("5 · network type", det.get("network_type") or "private / unreachable",
            fired=fired_rung == "network type"),
    ]
    stage("audience", "Audience route", "#sec-order",
          [P["audience_rule"]],
          "precedence: ad variant > campaign intent > CRM > work-email domain > network type",
          _branches(["enterprise", "selfserve", "research", "neutral"], P["audience"]),
          f"audience = {P['audience']}",
          "enterprise → sales emphasis; selfserve → trial/AUM emphasis; research → academic program",
          detail=aud_detail)

    # 9 · objection prioritize (includes the narrower track route)
    pri = P["objections"]["prioritized"]
    route = P["audience_route"]
    eligible = [o for o in OBJECTION_CATALOG if _objection_applies(o, route)]
    obj_detail = [_kv("Catalog", f"{len(OBJECTION_CATALOG)} objections · route {ROUTE_LABELS.get(route, route)} "
                                 f"filters to {len(eligible)} eligible")]
    for r in pri:
        obj_detail.append(_kv(f"#{r['rank']} {r['objection_id']} (score {r['score']})",
                              f"\u201c{r['text']}\u201d · signals: {', '.join(r['signal_source'])}",
                              pol="allude", fired=True))
    for a in P["objections"]["assignments"]:
        obj_detail.append(_kv(f"slot ← #{a['rank']}", f"{a['slot']} ← {a['objection_id']}"))
    for b in P["objections"]["blocked"]:
        obj_detail.append(_kv(f"blocked · {b['objection_id']}", f"\u201c{b['blocked_say']}\u201d", pol="hold"))
    stage("objections", "Objection prioritize", "#sec-objections",
          [f"track route = {ROUTE_LABELS.get(route, route)}"]
          + ([f"#{r['rank']} {r['objection_id']} (score {r['score']})" for r in pri] or ["no signals matched"]),
          "score OBJECTION_CATALOG signals → rank top 3–5 → weave into copy slots",
          _branches(list(ROUTE_LABELS.values()), ROUTE_LABELS.get(route, route)),
          (f"{len(pri)} objections ranked" if pri else "no objections matched"),
          "sales psychology meets them where they are — every reframe uses only verified claims",
          detail=obj_detail)

    # 10 · surface policy gate — per-slot say / allude / hold
    diff = P["copy_diff"]
    changed = [d for d in diff if d["changed"]]
    n_say = sum(1 for d in changed if d["policy"] == "say")
    n_allude = sum(1 for d in changed if d["policy"] == "allude")
    n_blocked = (sum(1 for d in diff if d.get("blocked_say"))
                 + len(P["objections"]["blocked"]))
    pol_detail = [_kv(d["label"], f"{'personalized' if d['changed'] else 'generic'} · source: {d['source']}",
                      pol=d["policy"] if d["changed"] else None, fired=d["changed"])
                  for d in diff]
    pol_detail += [_kv(f"blocked · {d['slot']}", f"\u201c{d['blocked_say']}\u201d", pol="hold")
                   for d in diff if d.get("blocked_say")]
    stage("policy", "Surface policy gate", "#sec-slots",
          [f"{d['slot']}: {d['policy']}" for d in changed] or ["(all slots generic)"],
          "say = recite · allude = shape only · hold = never ships",
          [{"label": f"say — recited ({n_say})", "taken": n_say > 0},
           {"label": f"allude — shaped ({n_allude})", "taken": n_allude > 0},
           {"label": f"hold — blocked ({n_blocked})", "taken": n_blocked > 0}],
          f"{len(changed)} of {len(diff)} slots personalized · {n_blocked} say variants blocked",
          "every personalized slot carries its source + policy; blocked recites appear only on /planet/dev",
          detail=pol_detail)

    # 11 · compose
    compose_detail = [
        _kv(f"order · {aud}", " → ".join(order), fired=P["audience"] == aud and P["order"] == order)
        for aud, order in ORDER_BY_AUDIENCE.items()
    ]
    if ad and ad["page"].get("order"):
        compose_detail.append(_kv(f"order · ad override ({ad['id']})",
                                  " → ".join(ad["page"]["order"]),
                                  fired=P["order"] == ad["page"]["order"]))
    stage("compose", "Compose page", "#sec-order",
          [f"audience = {P['audience']}"
           + (f" · ad variant order override ({ad['id']})" if ad and ad["page"].get("order") else "")],
          "ORDER_BY_AUDIENCE, unless the ad variant overrides",
          [],
          " → ".join(P["order"]),
          "same sections, same facts — only emphasis and order move",
          detail=compose_detail)

    # 13 · brain simulator — generate → score → select (when enabled)
    hi_ref = P["hero_image"]
    ir_ref = hi_ref.get("receipt") or {}
    brain = P.get("brain_sim") or brain_sim_signal(ir_ref)
    bs_taken = {
        "scored": "winner selected (scored)",
        "target_mapped": "target mapped (cache hit / no regen)",
        "pending": "not invoked",
        "disabled": "disabled",
    }.get(brain.get("mode", "pending"))
    bs_detail = [
        _kv("Enabled", "yes" if brain.get("enabled") else "no",
            fired=bool(brain.get("enabled"))),
        _kv("Intent", brain.get("intent_id") or ir_ref.get("intent_id") or "—"),
        _kv("brain_target", f"{brain.get('brain_target') or '—'} "
                            f"({brain.get('brain_target_label') or '—'})",
            fired=bool(brain.get("brain_target"))),
    ]
    if brain.get("brain_regions"):
        bs_detail.append(_kv("Regions", ", ".join(brain["brain_regions"])))
    if brain.get("brain_score") is not None:
        bs_detail.append(_kv("brain_score", f"{brain['brain_score']:.3f}",
                             fired=True))
        bs_detail.append(_kv("Simulator", brain.get("brain_simulator") or "proxy_v1"))
        if brain.get("candidates_evaluated"):
            bs_detail.append(_kv("Candidates evaluated", str(brain["candidates_evaluated"])))
        for region, val in sorted((brain.get("brain_region_scores") or {}).items(),
                                  key=lambda x: -x[1])[:4]:
            bs_detail.append(_kv(f"ROI · {region}", f"{val:.3f}"))
    else:
        bs_detail.append(_kv("Loop", "generate N → score → cache winner only",
                             fired=brain.get("enabled")))
        bs_detail.append(_kv("Override", "BRAIN_SIM_BEST_OF_N env var"))
    stage("brainsim", "Brain simulator", "#sec-brain-sim",
          [f"brain_target={brain.get('brain_target') or '—'}",
           f"intent={brain.get('intent_id') or ir_ref.get('intent_id') or '—'}"]
          + ([f"brain_score={brain['brain_score']:.3f}"] if brain.get("brain_score") is not None else []),
          brain.get("rule", "intent brain_target → BrainSimulatorScorer.select_best()"),
          _branches(["winner selected (scored)", "target mapped (cache hit / no regen)",
                     "not invoked", "disabled"],
                    bs_taken if brain.get("enabled") else "disabled"),
          brain.get("output", "—"),
          brain.get("why", "predicted visual-response optimization — not measured visitor brain data"),
          skipped=not brain.get("enabled"),
          skip_reason="brain_simulator.enabled: false for this tenant",
          detail=bs_detail)

    # 14 · hero image
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
    g_blocked = ir.get("guardrails_blocked") or []
    if g_blocked:
        hi_reads.append(f"guardrails_blocked={len(g_blocked)}")
    img_detail = []
    if sel.get("rule_fired"):
        img_detail.append(_kv("Intent rule fired", sel["rule_fired"], fired=True))
    img_detail += [_kv(k.replace("_", " ").capitalize(),
                       " → ".join(ir[k]) if k == "fallback_chain"
                       else (ir[k][:220] + "…" if k == "prompt" and len(str(ir[k])) > 220
                             else ir[k]))
                   for k in ("intent_id", "secondary_intent_id", "conversion_goal", "drives_action",
                             "prompt", "model", "vendor", "cache_key", "license",
                             "fallback_chain", "generated_at",
                             "brain_target", "brain_score", "brain_simulator",
                             "candidates_evaluated")
                   if ir.get(k) not in (None, "", [])]
    img_detail += [_kv("Guardrail applied", g, pol="hold") for g in g_blocked]
    if not img_detail:
        img_detail = [_kv("Receipt", "gradient fallback — no cache hit, no API key, no gallery match")]
    stage("heroimg", "Hero image resolve", "#sec-hero-image",
          hi_reads,
          "select_image_intent → build_structured_prompt → guardrails → cache → API → gallery → gradient",
          _branches(["generated", "pending", "gallery", "gradient"], src),
          f"source = {src} · intent = {ir.get('intent_id', '—')}",
          (f"intent {ir.get('intent_id')} ({ir.get('conversion_goal', '—')}) drives hero CTA; "
           f"{len(g_blocked)} guardrail(s) applied" if g_blocked else
           "structured prompt assembled from signals — page shell renders instantly"),
          detail=img_detail)

    # 15 · hero motion — timelapse loop (Planet only when motion.enabled)
    motion_receipt = (hi.get("motion_receipt") or ir.get("motion") or {})
    motion_enabled_flag = MG.motion_enabled(tenant=IMAGE_TENANT)
    m_src = motion_receipt.get("source", "pending" if motion_enabled_flag else "disabled")
    m_reads = [
        f"motion_status={hi.get('motion_status', '—')}",
        f"metaphor={motion_receipt.get('motion_metaphor', '—')}",
        f"assembly={motion_receipt.get('assembly', 'animated_webp')}",
    ]
    if motion_receipt.get("cache_key"):
        m_reads.append(f"cache_key={motion_receipt['cache_key'][:12]}…")
    m_detail = [
        _kv("Framing", motion_receipt.get("framing") or MG.motion_settings(tenant=IMAGE_TENANT).get("framing"),
            fired=bool(motion_receipt.get("framing"))),
        _kv("Motion metaphor", motion_receipt.get("motion_metaphor", "—"),
            fired=bool(motion_receipt.get("motion_metaphor"))),
        _kv("Assembly", motion_receipt.get("assembly", "animated_webp")),
        _kv("Duration", f"{motion_receipt.get('duration_ms', 3000)} ms loop"),
    ]
    for fr in motion_receipt.get("frames") or []:
        m_detail.append(_kv(f"Frame {fr.get('label', fr.get('index'))}",
                              fr.get("image_url") or fr.get("image_path", "—")))
    if motion_receipt.get("change_legibility_mean") is not None:
        m_detail.append(_kv("Change legibility (mean)",
                              f"{motion_receipt['change_legibility_mean']:.3f}", fired=True))
    stage("heromotion", "Hero motion loop", "#sec-hero-motion",
          m_reads,
          "intent motion_metaphor → N keyframe prompts → assemble animated WebP → cache",
          _branches(["generated", "pending", "unavailable", "disabled"], m_src),
          (f"source = {m_src} · {motion_receipt.get('motion_metaphor', '—')}"
           if motion_enabled_flag else "motion disabled"),
          motion_receipt.get("framing") or "Simulated change-over-time — not visitor neuro-stimulation",
          skipped=not motion_enabled_flag,
          skip_reason="motion.enabled: false for this tenant",
          detail=m_detail)

    return {"inputs": inputs, "stages": stages}


def sample_login_email() -> str:
    """The cohort email published on the showcase card (synthetic)."""
    return "amara.diallo@meridianagronomy.com"


def sample_magic_token() -> str:
    """The magic token embedded in the sample email entry link (synthetic recipient)."""
    return CO.magic_token(CO.BY_ID["kofi"])
