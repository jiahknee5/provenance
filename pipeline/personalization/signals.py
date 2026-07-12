"""The personalization signal catalog — every fact a website could use, and where it comes from.

This is the heart of the demo. Each `Signal` is a single thing a site might know about a
visitor, bound to:

  • source        — WHERE it comes from (the provenance class). One of:
                    observed · first_party · declared · oauth · broker · identity_graph
  • vendor / how  — the concrete real-world way you'd actually obtain it (a product + method)
  • tier          — the unlock gate at which it first becomes available (anonymous → … → full)
  • cost          — what it costs to acquire (honest: $0 for what we observe, $ for brokers)
  • basis         — the lawful/consent posture
  • creepiness     — 1 (banal) … 5 (skin-crawl)
  • surface        — say / allude / hold: the SAME control the funnel uses (anti-creepiness)
  • creepy         — the literal sentence the *creepy* renderer prints (with provenance tag)

Values are synthesized for ONE deterministic persona (`PERSONA` below: "Maya"). The catalog
is reference data — no connector here calls a paid API; the broker/identity rows are
*documented*, not invoked (mirrors pipeline/enrichment/catalog.py).
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.customer.schemas import SurfacePolicy

SAY, ALLUDE, HOLD = SurfacePolicy.SAY, SurfacePolicy.ALLUDE, SurfacePolicy.HOLD

# --------------------------------------------------------------------------- #
# Provenance classes — WHERE personalization data comes from.
# --------------------------------------------------------------------------- #
OBSERVED = "observed"            # collected by us, passively, at page load (HTTP + JS)
FIRST_PARTY = "first_party"      # our own logs / CRM — behavior we recorded, data we hold
DECLARED = "declared"            # the visitor typed it / handed it to us
OAUTH = "oauth"                  # granted via "Sign in with Google" scopes
BROKER = "broker"                # purchased from a 3rd-party data broker / append
IDENTITY_GRAPH = "identity_graph"  # cross-device + offline match bought from an ID-resolution vendor

SOURCE_META = {
    OBSERVED: {
        "label": "Collected ourselves (passive)",
        "where": "The HTTP request + a few lines of JavaScript, the instant the page loads. "
                 "No login, no form, often no cookie. You give it to every site you visit.",
        "cost": "$0 (optionally a few ¢ for a reverse-IP or fingerprint lookup)",
        "color": "obs",
    },
    FIRST_PARTY: {
        "label": "Our own database",
        "where": "Behaviour we logged on previous visits (cookies / device match) and records "
                 "in our CRM. We already own it — no third party involved.",
        "cost": "$0 (we collected it)",
        "color": "fp",
    },
    DECLARED: {
        "label": "Declared by the visitor",
        "where": "A field they filled in — a newsletter box, a lead form, an account signup. "
                 "The cleanest data there is: they chose to tell us.",
        "cost": "$0",
        "color": "dec",
    },
    OAUTH: {
        "label": "Granted via Google sign-in",
        "where": "\"Sign in with Google\" hands us OAuth scopes. Profile is one click; but the "
                 "consent screen can also grant calendar, Gmail metadata, YouTube, contacts and "
                 "location history — an enormous jump for one tap.",
        "cost": "$0 (the price is the permission)",
        "color": "oauth",
    },
    BROKER: {
        "label": "Purchased (data broker append)",
        "where": "Match a name+email+address against a data broker (Acxiom, Experian, Epsilon, "
                 "Oracle Data Cloud) and append what they've compiled: income, life events, "
                 "demographics, propensities. Billions of attributes, sold per record.",
        "cost": "~$0.05–0.25 per record matched",
        "color": "brk",
    },
    IDENTITY_GRAPH: {
        "label": "Identity graph (cross-device + offline)",
        "where": "An identity-resolution vendor (LiveRamp, Tapad) ties this browser to your other "
                 "devices, your household, and offline data sold by retailers — loyalty cards, "
                 "credit-card panels, smart-TV viewing. The complete picture.",
        "cost": "$$ platform subscription",
        "color": "idg",
    },
}

# --------------------------------------------------------------------------- #
# Tiers — escalating unlock gates. Each adds new provenance classes; higher tiers
# inherit everything below them. This is the "landing page → Google login → everything"
# escalation the brief asks for.
# --------------------------------------------------------------------------- #
TIERS = [
    {"id": "anonymous", "label": "Anonymous landing", "login": "none",
     "blurb": "First hit. No login, no form, cookies cleared. Just an HTTP request and a little JS.",
     "adds": [OBSERVED]},
    {"id": "returning", "label": "Returning visitor", "login": "cookie",
     "blurb": "We've seen this browser before (a cookie, or a device fingerprint that survives clearing it).",
     "adds": [FIRST_PARTY]},
    {"id": "email", "label": "Identified — gave email", "login": "email",
     "blurb": "They dropped an email into a newsletter or 'more info' box. Now they're a name, not an IP.",
     "adds": [DECLARED]},
    {"id": "google", "label": "Signed in with Google", "login": "google",
     "blurb": "One tap on 'Sign in with Google'. The single biggest jump in what a site can know.",
     "adds": [OAUTH]},
    {"id": "broker", "label": "+ Purchased append", "login": "google",
     "blurb": "We pay a data broker to append everything they've compiled against that identity.",
     "adds": [BROKER]},
    {"id": "crm", "label": "+ Existing customer", "login": "google",
     "blurb": "They're already in our database from a past purchase — so we layer our own CRM on top.",
     "adds": [FIRST_PARTY]},
    {"id": "everything", "label": "Full identity graph", "login": "google",
     "blurb": "The complete creepy maximum: cross-device, household, and offline purchase data, fused.",
     "adds": [IDENTITY_GRAPH]},
]
TIER_ORDER = {t["id"]: i for i, t in enumerate(TIERS)}
TIER_BY_ID = {t["id"]: t for t in TIERS}


@dataclass(frozen=True)
class Signal:
    id: str
    label: str                 # the data point, in plain words
    value: str                 # the synthesized value for the persona
    source: str                # provenance class (one of the constants above)
    vendor: str                # the real product/method you'd use to get it
    how: str                   # one line: literally how it's acquired
    tier: str                  # the tier at which it unlocks
    cost: str                  # acquisition cost
    basis: str                 # lawful / consent posture
    creepiness: int            # 1..5
    surface: SurfacePolicy     # responsible default: say / allude / hold
    creepy: str                # the literal sentence creepy-mode prints

    @property
    def source_label(self) -> str:
        return SOURCE_META[self.source]["label"]


# A vivid, entirely synthetic persona. "Current time" is part of the persona (fixed at
# 11:47pm) so the demo is deterministic — no wall clock, no RNG.
PERSONA = {
    "handle": "this visitor",
    "name": "Maya Chen",
    "first": "Maya",
    "city": "Austin, Texas",
    "note": "100% synthetic. No real person; no real PII. Every value below is fabricated to "
            "show what each data source *would* yield.",
}

# --------------------------------------------------------------------------- #
# THE CATALOG. Ordered by tier so the escalation reads top-to-bottom.
# --------------------------------------------------------------------------- #
CATALOG: list[Signal] = [
    # ---- TIER 0 · ANONYMOUS LANDING — collected ourselves, at page load, $0 -------------
    Signal("ip_city", "Approximate location", "Austin, Texas (metro)", OBSERVED,
           "MaxMind GeoIP2 / IP2Location", "Resolve the visitor's IP address to a city.",
           "anonymous", "$0 (free GeoIP DB)", "implied — you connected to us", 2, ALLUDE,
           "You're in Austin, Texas."),
    Signal("ip_zip", "Neighborhood", "~2 mi of ZIP 78722 (Mueller)", OBSERVED,
           "IP geolocation (ZIP-level)", "Same IP lookup, at neighborhood resolution.",
           "anonymous", "$0", "implied", 3, HOLD,
           "…within about two miles of the 78722 ZIP — the Mueller neighborhood."),
    Signal("isp", "Connection", "Spectrum cable · residential", OBSERVED,
           "IP → ISP / ASN lookup", "Map the IP to its owning network and connection type.",
           "anonymous", "$0", "implied", 2, ALLUDE,
           "On a residential Spectrum line — so you're at home, not the office."),
    Signal("revip_company", "Company (reverse-IP)", "(residential — no company match)", OBSERVED,
           "Clearbit Reveal / KickFire", "Match the IP to a company's network to de-anonymize B2B visits.",
           "anonymous", "~$0.01 / lookup", "account-level (no PII)", 2, ALLUDE,
           "If this were an office IP we'd already know your employer — yours is residential, so: working from home."),
    Signal("device", "Device & OS", "Apple iPhone 13 · iOS 17.4 · Safari", OBSERVED,
           "User-Agent + Client Hints", "The browser announces device, OS and version on every request.",
           "anonymous", "$0", "implied (sent by your browser)", 1, ALLUDE,
           "On an iPhone 13 running iOS 17.4, in Safari."),
    Signal("device_tier", "Device economics", "≈2-yr-old, non-Pro model", OBSERVED,
           "Model → release-date + price tier", "Infer age and price bracket from the device model.",
           "anonymous", "$0", "inferred", 3, HOLD,
           "A two-year-old, non-Pro phone — we can guess your budget from your hardware."),
    Signal("screen_mode", "Screen & theme", "390×844 · dark mode · battery-saver on", OBSERVED,
           "JS: screen, prefers-color-scheme", "A few JS properties read on load.",
           "anonymous", "$0", "implied", 1, ALLUDE,
           "Dark mode, battery-saver on, one tab open."),
    Signal("battery", "Battery level", "18% and dropping (not charging)", OBSERVED,
           "Battery Status API", "JS reads the device battery level and charging state.",
           "anonymous", "$0", "implied (where supported)", 4, HOLD,
           "Your battery's at 18% and falling — better make this quick."),
    Signal("localtime", "Local time", "11:47 PM, Tuesday", OBSERVED,
           "JS Date + IANA timezone", "The browser's clock and timezone, read in JS.",
           "anonymous", "$0", "implied", 2, ALLUDE,
           "It's 11:47 PM on a Tuesday where you are — a late-night browse."),
    Signal("language", "Languages", "en-US, then zh-CN", OBSERVED,
           "Accept-Language header", "The ranked language list your browser sends.",
           "anonymous", "$0", "implied", 2, HOLD,
           "Your browser lists Chinese as a second language — a hint about who you are."),
    Signal("referrer", "Where you came from", "Instagram ad · campaign 'career_switch_q3'", OBSERVED,
           "Referrer + UTM parameters", "The link that sent you carries the campaign + creative.",
           "anonymous", "$0", "implied", 2, ALLUDE,
           "You came from our Instagram ad — the 'from barista to AI engineer' creative."),
    Signal("fingerprint", "Device fingerprint", "fp_9f3a… (canvas+fonts+GPU hash)", OBSERVED,
           "FingerprintJS", "Hash your canvas, fonts and GPU into an ID that survives clearing cookies.",
           "anonymous", "~$0.005 / match (pro tier)", "no consent needed — that's the problem", 5, HOLD,
           "Even with cookies off, this exact device hashes to fp_9f3a — we'll recognize you on your next 'anonymous' visit."),

    # ---- TIER 1 · RETURNING VISITOR — our own first-party behavioral logs ----------------
    Signal("visits", "Visit history", "4th visit in 6 days", FIRST_PARTY,
           "First-party cookie / fingerprint", "Tie this session to prior ones we logged.",
           "returning", "$0", "first-party + notice", 2, ALLUDE,
           "This is your 4th visit in 6 days."),
    Signal("pages", "What you looked at", "'Night cohort' ×3, pricing ×2", FIRST_PARTY,
           "Site analytics", "Every page, in order, time-stamped.",
           "returning", "$0", "first-party + notice", 3, ALLUDE,
           "You keep returning to the night cohort and the pricing page."),
    Signal("dwell", "How you read", "Read 90% of the financing FAQ, 2m11s", FIRST_PARTY,
           "Scroll-depth + dwell tracking", "JS records scroll position and time on each block.",
           "returning", "$0", "first-party + notice", 3, ALLUDE,
           "You read 90% of the financing FAQ and lingered two minutes."),
    Signal("abandoned", "Unfinished actions", "Started the application, didn't submit", FIRST_PARTY,
           "Form analytics", "Partial form state captured field-by-field, before submit.",
           "returning", "$0", "first-party + notice", 3, ALLUDE,
           "You started the application Sunday and didn't finish it."),
    Signal("retarget", "Ad retargeting pool", "Meta audience 'career-switch-warm' · shown 7 ads", BROKER,
           "Meta Pixel / Google Ads tag", "A 3rd-party pixel adds you to ad audiences across the web.",
           "returning", "ad spend", "disclosed tracking; pixel is 3rd-party", 4, HOLD,
           "You're in our Meta retargeting pool — that's why we've chased you across Instagram seven times."),
    Signal("crosssite", "Comparison shopping", "Visited 2 competitor bootcamps this week", BROKER,
           "DMP / cookie-sync (Lotame, Oracle BlueKai)", "Cross-site browsing bought from a data-management platform.",
           "returning", "$$ subscription", "3rd-party cookie — degrading, but still real", 5, HOLD,
           "We can see you comparison-shopped two competitors this week."),

    # ---- TIER 2 · GAVE EMAIL — declared, plus what an email hash unlocks ------------------
    Signal("d_name", "Name", "Maya", DECLARED,
           "Newsletter / lead form", "They typed it into a field.",
           "email", "$0", "declared — they told us", 1, SAY,
           "Hi Maya,"),
    Signal("d_email", "Email", "maya.chen@gmail.com", DECLARED,
           "Form field", "They typed it.",
           "email", "$0", "declared", 1, SAY,
           "…at maya.chen@gmail.com."),
    Signal("d_goal", "Stated goal", "\"switch into AI without going broke\"", DECLARED,
           "Free-text form field", "They wrote it in their own words.",
           "email", "$0", "declared", 1, SAY,
           "You told us you want to switch into AI without going broke."),
    Signal("e_gravatar", "Linked photo & accounts", "Gravatar photo + 9 sites tied to this email", OBSERVED,
           "Gravatar / hash lookup", "Hash the email and look it up across services.",
           "email", "$0", "the hash is public; the linkage isn't expected", 4, HOLD,
           "Your email hash pulls a profile photo and nine other accounts tied to it."),
    Signal("e_breach", "Breach exposure", "Appears in 3 known breaches", OBSERVED,
           "Have I Been Pwned", "Check the email against breach corpora.",
           "email", "$0", "public breach data", 4, HOLD,
           "That email shows up in three known data breaches."),

    # ---- TIER 3 · SIGN IN WITH GOOGLE — OAuth scopes. The big jump. ----------------------
    Signal("g_profile", "Verified name & photo", "Maya Chen + verified profile photo", OAUTH,
           "Google OAuth · profile scope", "One click grants name, photo, locale.",
           "google", "$0 (consented)", "explicit OAuth consent", 1, SAY,
           "Welcome, Maya Chen 👋"),
    Signal("g_email", "Verified email + recovery", "maya.chen@gmail.com (verified) · recovery phone on file", OAUTH,
           "Google OAuth · email scope", "Verified address, and that a recovery phone exists.",
           "google", "$0 (consented)", "OAuth consent", 2, ALLUDE,
           "…verified, with a recovery phone on file."),
    Signal("g_age", "Account maturity", "Google account since 2009 · 'power user'", OAUTH,
           "Profile metadata", "Account age and activity hints.",
           "google", "$0", "OAuth consent", 2, ALLUDE,
           "You've had this Google account since 2009 — a heavy user."),
    Signal("g_calendar", "Your calendar", "'OB checkup Thu 2pm', 'daycare tour Sat'", OAUTH,
           "Google OAuth · calendar.readonly", "The consent screen can include calendar read — most people don't notice.",
           "google", "$0 (one extra checkbox)", "OAuth scope — easy to over-grant", 5, HOLD,
           "Your calendar has an OB checkup Thursday and a daycare tour Saturday."),
    Signal("g_gmail", "Inbox metadata", "Receipts from Pampers, BuyBuyBaby, a fertility clinic", OAUTH,
           "Google OAuth · gmail.metadata", "Senders + subjects reveal purchases without reading bodies.",
           "google", "$0", "OAuth scope", 5, HOLD,
           "Your inbox has receipts from Pampers and a fertility clinic."),
    Signal("g_youtube", "Watch history", "Recently: 'newborn sleep', 'career switch at 34'", OAUTH,
           "Google OAuth · YouTube Data API", "Watch + search history as interest signals.",
           "google", "$0", "OAuth scope", 4, HOLD,
           "You've been watching newborn-sleep videos and career-switch talks."),
    Signal("g_location", "Location history", "Home: Mueller · work: downtown · 2 hospital visits this month", OAUTH,
           "Google OAuth · Maps Timeline", "Months of timestamped places.",
           "google", "$0", "OAuth scope", 5, HOLD,
           "Your location history shows home, work, and two hospital visits this month."),
    Signal("g_contacts", "Contacts graph", "1,840 contacts · partner 'Jordan', an OB-GYN, your mom", OAUTH,
           "Google OAuth · People API", "Your whole address book, with labels.",
           "google", "$0", "OAuth scope", 4, HOLD,
           "Your contacts include Jordan, your mom, and an OB-GYN."),

    # ---- TIER 4 · PURCHASED APPEND — data broker, PII-matched ----------------------------
    Signal("b_income", "Household income", "Modeled $115–135K band", BROKER,
           "Experian / Acxiom income model", "Append modeled income to a name+address match.",
           "broker", "~$0.05–0.25 / record", "broker AUP + your basis", 4, HOLD,
           "Your household income is modeled at $115–135K."),
    Signal("b_home", "Home & residence", "Homeowner · ~$540K home · 4 yrs in residence", BROKER,
           "Property records / Acxiom", "Public deeds + broker compilation.",
           "broker", "bundled in append", "public record + append", 3, ALLUDE,
           "You own a ~$540K home and have lived there four years."),
    Signal("b_networth", "Net worth band", "$250–500K", BROKER,
           "Experian wealth model", "Modeled from assets, home, credit.",
           "broker", "bundled", "modeled", 4, HOLD,
           "Estimated net worth: a quarter to half a million."),
    Signal("b_separated", "Life event: separation", "Trigger: 'recently separated'", BROKER,
           "Epsilon / Experian life-event triggers", "Brokers sell change-of-status triggers as they happen.",
           "broker", "premium trigger", "sensitive — exactly what shouldn't be used", 5, HOLD,
           "A life-event trigger flags you as recently separated."),
    Signal("b_newparent", "Life event: new baby", "Trigger: 'new parent', infant 0–6mo", BROKER,
           "Epsilon life-event triggers", "New-parent is one of the most-traded triggers.",
           "broker", "premium trigger", "sensitive", 5, HOLD,
           "Another flags a brand-new baby, zero to six months old."),
    Signal("b_auto", "Vehicle", "Drives a 2021 Subaru Outback", BROKER,
           "Oracle Data Cloud / Polk auto", "Registration + service data compiled and sold.",
           "broker", "bundled", "append", 3, ALLUDE,
           "You drive a 2021 Subaru Outback."),
    Signal("b_edu", "Education & occupation", "BS · occupation: software/IT", BROKER,
           "Acxiom InfoBase", "Compiled demographics.",
           "broker", "bundled", "append", 2, ALLUDE,
           "Bachelor's degree, working in software."),
    Signal("b_politics", "Political profile", "Leans Democrat · high turnout · past donor", BROKER,
           "L2 / Aristotle voter file", "Voter rolls + modeling, sold for targeting.",
           "broker", "voter-file license", "sensitive (political)", 5, HOLD,
           "Voter-file modeling pegs you as a likely-Democrat, likely-donor."),
    Signal("b_health", "Health ad audiences", "'Expectant/new parent', 'seasonal allergy sufferer'", BROKER,
           "Health-adjacent ad audiences", "Inferred condition audiences sold for ad targeting.",
           "broker", "audience license", "sensitive (health-adjacent)", 5, HOLD,
           "You're in two health audiences: new-parent and allergy-sufferer."),
    Signal("b_ethnic", "Ethnic affinity", "Modeled: Chinese", BROKER,
           "Acxiom ethnic-affinity model", "Name + geography modeled into an 'affinity'.",
           "broker", "bundled", "sensitive (protected class)", 5, HOLD,
           "A model assigns you a 'Chinese' ethnic affinity."),
    Signal("b_propensity", "In-market signals", "Minivan, baby gear, term life insurance", BROKER,
           "Bombora / Oracle propensity", "Predicted near-term purchases.",
           "broker", "subscription", "modeled", 3, HOLD,
           "You're modeled as in-market for a minivan, baby gear and life insurance."),

    # ---- TIER 5 · EXISTING CUSTOMER — our own CRM ----------------------------------------
    Signal("c_customer", "Customer history", "Took 'Intro to Python' with us, 2023", FIRST_PARTY,
           "Our CRM", "We already have an account record.",
           "crm", "$0 (we own it)", "first-party customer relationship", 1, SAY,
           "Good to have you back — you took Intro to Python with us in 2023."),
    Signal("c_ltv", "Spend & support", "LTV $349 · 1 purchase · 3 support tickets", FIRST_PARTY,
           "CRM / billing", "Lifetime value and support load.",
           "crm", "$0", "first-party", 2, ALLUDE,
           "Lifetime spend $349, and you've opened three support tickets."),
    Signal("c_churn", "Risk segment", "Churn-risk 0.31 · 'price-sensitive'", FIRST_PARTY,
           "Internal model", "A score we computed on our own data.",
           "crm", "$0", "first-party, internal", 3, HOLD,
           "Our model tags you 'price-sensitive', churn-risk 0.31 — so we'd quietly lead with a discount."),
    Signal("c_card", "Payment on file", "Visa •••• 4242, exp 11/26", FIRST_PARTY,
           "Billing system", "Stored from the last purchase.",
           "crm", "$0", "first-party; PCI-scoped", 3, HOLD,
           "We've still got your Visa ending 4242 on file."),
    Signal("c_nps", "Advocacy", "NPS 9 · left a public 5★ review", FIRST_PARTY,
           "Survey + reviews", "Your own feedback to us.",
           "crm", "$0", "first-party", 1, SAY,
           "Thanks again for the 5-star review."),

    # ---- TIER 6 · FULL IDENTITY GRAPH — cross-device + offline, fused --------------------
    Signal("i_devices", "Cross-device", "This iPhone + a work MacBook + a home iPad = one you", IDENTITY_GRAPH,
           "LiveRamp / Tapad", "Deterministic + probabilistic linking of all your devices.",
           "everything", "$$ subscription", "linkage you never explicitly authorized", 5, HOLD,
           "This phone, a work laptop and a home iPad all resolve to one person — you."),
    Signal("i_household", "Household", "2 adults (Maya, Jordan) + 1 infant", IDENTITY_GRAPH,
           "LiveRamp household graph", "Devices + addresses clustered into a household.",
           "everything", "$$", "household-level inference", 5, HOLD,
           "Your household: two adults and one infant, all mapped."),
    Signal("i_loyalty", "Offline purchases", "Target loyalty: diapers + formula weekly; Whole Foods 3×/wk", IDENTITY_GRAPH,
           "Retail loyalty data resold to brokers", "Loyalty-card baskets sold and matched to your identity.",
           "everything", "$$", "you joined for points; resale was buried in the terms", 5, HOLD,
           "Your Target runs — diapers, formula, weekly — are in the file too."),
    Signal("i_cards", "Card-spend panel", "Baby-gear spike; $0 restaurants since April", IDENTITY_GRAPH,
           "Credit-card transaction panels", "Anonymized-then-rematched card data sold to marketers.",
           "everything", "$$", "'anonymized' — then re-identified", 5, HOLD,
           "A credit-card panel shows a baby-gear spike and zero restaurant spend since April."),
    Signal("i_acr", "Smart-TV viewing", "Heavy HGTV + late-night cartoons", IDENTITY_GRAPH,
           "Smart-TV ACR (Samba, Vizio Inscape)", "Your TV reports what's on screen, frame-matched.",
           "everything", "$$", "buried in the TV's setup screen", 5, HOLD,
           "Your TV's been streaming a lot of HGTV — and cartoons, late at night."),
]

CATALOG_BY_ID = {s.id: s for s in CATALOG}


def available_at(tier: str) -> list[Signal]:
    """Every signal unlocked at `tier` or any lower tier (tiers are monotonic)."""
    cap = TIER_ORDER[tier]
    return [s for s in CATALOG if TIER_ORDER[s.tier] <= cap]


def unlocked_by(tier: str) -> list[Signal]:
    """Only the signals that newly unlock *at* this tier (the per-step delta)."""
    return [s for s in CATALOG if s.tier == tier]
