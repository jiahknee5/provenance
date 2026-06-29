"""The /demo spec — 3 visitor scenarios, each with 3 GATED variants (bandit arms) plus one
BLOCKED "ungated" variant, and a master-KPI tree.

This is the single source of truth that ties **data → variant → KPI**, so the demo page,
the cloner injection, the bandit simulation, and the monitor all read the same definitions
and can never drift apart.

Provenance is first-class: every gated variant lists exactly the signals it used, each with
its source class and surface policy (`say` / `allude` / `hold`). The invariant the tests
enforce: **no gated variant's copy uses a `hold` fact** — a hold fact may only *steer*
(its role is "steers, not shown"). The BLOCKED variant per scenario is the "creepy / ungated"
arm: it would win on engagement but is kept out of the action pool by the surface policy —
mirroring the Optimizer's planted-lie arm, so the bandit provably cannot select it.

All synthetic, deterministic. KPI movement is a *simulated* reinforcement-learning result
(see demo_sim.py), never real traffic.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Provenance source classes (mirror pipeline.personalization.signals)
OBSERVED = "observed"
FIRST_PARTY = "first_party"
DECLARED = "declared"
ENRICH = "enrich"            # vendor person/company enrichment (PDL etc.)
BOUGHT = "bought"            # reverse-IP / broker append
BROKER = "broker"

SOURCE_LABEL = {
    OBSERVED: "Observed at load",
    FIRST_PARTY: "First-party (CRM / behaviour)",
    DECLARED: "Declared by the visitor",
    ENRICH: "Enrichment (PDL)",
    BOUGHT: "Bought (reverse-IP)",
    BROKER: "Broker append",
}

SAY, ALLUDE, HOLD = "say", "allude", "hold"

# Where on the cloned site a variant maps — drives cloner injection + the demo receipt rail.
# Each entry: (label, where-on-the-page, what-it-changes).
PLACEMENT = {
    "hero":   ("Hero", "top of the page, above the fold", "replaces the lead headline + CTA"),
    "banner": ("Banner", "a slim strip below the site's own header", "adds a contextual line"),
    "cta":    ("Offer / CTA", "next to the primary call-to-action", "reframes the offer + button"),
    "theme":  ("Page theme", "the whole page", "restyles tone + leads with a matched angle"),
}


@dataclass(frozen=True)
class DataUse:
    signal: str        # the concrete signal, e.g. "daypart 11:47pm"
    source: str        # provenance class
    policy: str        # say / allude / hold
    role: str          # what it actually did on the page

    @property
    def source_label(self) -> str:
        return SOURCE_LABEL.get(self.source, self.source)


@dataclass(frozen=True)
class Variant:
    id: str            # "A1"
    label: str         # short component name
    headline: str
    sub: str
    cta: str
    accent: str        # hex
    kpi: str           # master-KPI key it targets
    data_used: list[DataUse]
    surface_note: str
    dark: bool = False
    blocked: bool = False   # the ungated "creepy" arm — kept OUT of the action pool
    placement: str = "hero"  # where on the cloned site it maps (PLACEMENT key)

    @property
    def arm(self) -> str:
        return self.id

    @property
    def place(self) -> tuple[str, str, str]:
        """(label, where-on-the-page, what-it-changes) for the receipt rail."""
        return PLACEMENT.get(self.placement, PLACEMENT["hero"])

    @property
    def place_label(self) -> str:
        return self.place[0]

    @property
    def uses_hold_in_copy(self) -> bool:
        """True only if a hold fact is marked as said/shown (the thing tests forbid)."""
        return any(d.policy == HOLD and "steer" not in d.role.lower()
                   and "never" not in d.role.lower() for d in self.data_used)


@dataclass(frozen=True)
class Scenario:
    id: str            # "A"
    key: str           # the identity key held
    label: str
    blurb: str
    available: list[str]          # data ribbon chips
    variants: list[Variant]       # 3 gated + 1 blocked


# --------------------------------------------------------------------------- #
# Master business KPI tree — each leaf is a real funnel metric a variant moves.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Kpi:
    key: str
    label: str
    group: str          # acquisition / activation / revenue
    unit: str
    direction: str      # "up" or "down" (down = lower is better, e.g. bounce)
    baseline: float
    target: float


KPIS: dict[str, Kpi] = {
    "bounce":        Kpi("bounce", "Bounce rate", "acquisition", "%", "down", 58.0, 42.0),
    "ctr":           Kpi("ctr", "Hero CTR", "acquisition", "%", "up", 4.0, 9.0),
    "lead_to_app":   Kpi("lead_to_app", "Lead → application", "acquisition", "%", "up", 12.0, 22.0),
    "reactivation":  Kpi("reactivation", "Dormant reactivation", "activation", "%", "up", 6.0, 15.0),
    "paid_conv":     Kpi("paid_conv", "Paid conversion", "revenue", "%", "up", 3.5, 7.0),
    "b2b_demo":      Kpi("b2b_demo", "B2B demo requests", "revenue", "per 1k", "up", 2.0, 6.0),
}

KPI_GROUPS = ["acquisition", "activation", "revenue"]


# --------------------------------------------------------------------------- #
# THE SCENARIOS
# --------------------------------------------------------------------------- #
SCENARIOS: list[Scenario] = [
    Scenario(
        id="A", key="IP + browser signals (no identity)",
        label="New anonymous viewer",
        blurb="First hit. No login, no form, no cookie — just the HTTP request and a little JS.",
        available=["geo / city", "daypart", "device", "referrer / UTM", "connection", "reverse-IP company (buy)"],
        variants=[
            Variant("A1", "Daypart adaptive theme",
                    "Late nights are when the big decisions get made.",
                    "{brand} — right here whenever you are, even at 11:47 PM.",
                    "Take a look", "#4cc4d4", "bounce", dark=True, placement="theme",
                    data_used=[
                        DataUse("daypart 11:47pm", OBSERVED, ALLUDE, "themes the page dark + 'late nights' angle"),
                        DataUse("IP → Austin", OBSERVED, ALLUDE, "local hello"),
                        DataUse("device: mobile", OBSERVED, ALLUDE, "mobile-dense layout"),
                        DataUse("UTM creative", OBSERVED, ALLUDE, "hero echoes the ad"),
                    ],
                    surface_note="observed · allude · no name"),
            Variant("A2", "B2B peer-logo hero",
                    "Teams at firms like yours already use {brand}.",
                    "The version of {brand} built for whole teams, not just individuals.",
                    "See it for teams", "#1d4ed8", "b2b_demo", placement="hero",
                    data_used=[
                        DataUse("reverse-IP → employer", BOUGHT, ALLUDE, "employer-level hero (~$0.01)"),
                        DataUse("company industry", BOUGHT, ALLUDE, "tailors the proof"),
                    ],
                    surface_note="bought · allude · company, not person"),
            Variant("A3", "Local-proof badge",
                    "{brand} is catching on in Austin.",
                    "See what people near you are choosing.",
                    "See local picks", "#2bb673", "ctr", placement="banner",
                    data_used=[DataUse("IP → city (Austin)", OBSERVED, ALLUDE, "local-proof framing")],
                    surface_note="observed · allude"),
            Variant("Ax", "Recognize-return (ungated)",
                    "Welcome back — third look this week?",
                    "We recognised your device even with cookies cleared.",
                    "Pick up where you left off", "#e0524a", "ctr", blocked=True, placement="banner",
                    data_used=[DataUse("device fingerprint (cookies cleared)", OBSERVED, HOLD,
                                        "would recite a recognised return — never shown")],
                    surface_note="HOLD — blocked by surface policy; the bandit cannot pull it"),
        ],
    ),
    Scenario(
        id="B", key="Email + name + your CRM history",
        label="Existing customer (email match)",
        blurb="Matched to your CRM + an append — all eight segment families are live.",
        available=["CRM lifecycle / LTV", "page & email behaviour", "declared goal",
                   "PDL: title / history", "broker income (buy)"],
        variants=[
            Variant("B1", "Welcome-back resume",
                    "Welcome back to {brand}, Maya.",
                    "Pick up right where you left off.",
                    "Continue", "#d98a16", "reactivation", placement="hero",
                    data_used=[
                        DataUse("CRM: first bought in 2023", FIRST_PARTY, SAY, "referenced warmly"),
                        DataUse("last-viewed item", FIRST_PARTY, ALLUDE, "deep-links back to it"),
                        DataUse("lifecycle: customer", FIRST_PARTY, SAY, "'welcome back' framing"),
                    ],
                    surface_note="say + allude"),
            Variant("B2", "Tailored-offer module",
                    "Maya, an offer on {brand} picked for you.",
                    "A few ways to make it fit your budget.",
                    "See your offer", "#2bb673", "paid_conv", placement="cta",
                    data_used=[
                        DataUse("declared name", DECLARED, SAY, "greeting"),
                        DataUse("price-page visits", FIRST_PARTY, ALLUDE, "leads with value/affordability"),
                        DataUse("modeled income", BROKER, HOLD, "steers the angle — never shown in copy"),
                    ],
                    surface_note="say + allude; income HOLD (steers, never shown)"),
            Variant("B3", "Prestige / peer hero",
                    "Leaders in your field choose {brand}.",
                    "Built for senior professionals like you.",
                    "Learn more", "#7e8ea3", "lead_to_app", placement="hero",
                    data_used=[
                        DataUse("PDL seniority", ENRICH, ALLUDE, "prestige framing"),
                        DataUse("PDL industry", ENRICH, ALLUDE, "industry proof"),
                    ],
                    surface_note="enrich · allude"),
            Variant("Bx", "Income-recite (ungated)",
                    "On a $190K income, {brand} is an easy yes, Maya.",
                    "We modeled your household income and net worth.",
                    "Pay in full", "#e0524a", "paid_conv", blocked=True, placement="cta",
                    data_used=[DataUse("modeled income / net worth", BROKER, HOLD,
                                        "would recite purchased income — never shown")],
                    surface_note="HOLD — blocked by surface policy; the bandit cannot pull it"),
        ],
    ),
    Scenario(
        id="C", key="Email + live click behaviour (magic-link)",
        label="Emailed lead who clicked",
        blurb="The click identifies them with no login and tells you exactly what they care about.",
        available=["declared (opt-in)", "email opens", "which CTA clicked", "pages / dwell",
                   "abandoned forms", "PDL: role", "cross-site (buy)"],
        variants=[
            Variant("C1", "Click-continuity",
                    "More of what you just clicked, Darnell.",
                    "Right where you left off on {brand}.",
                    "Keep going", "#2bb673", "lead_to_app", placement="hero",
                    data_used=[
                        DataUse("which link clicked", FIRST_PARTY, ALLUDE, "page continues the click"),
                        DataUse("declared interest", DECLARED, SAY, "quotes their stated interest"),
                        DataUse("PDL role", ENRICH, ALLUDE, "role-tailored proof"),
                    ],
                    surface_note="allude + say · magic-link, no login"),
            Variant("C2", "Resume / abandoned",
                    "You left something on {brand} — finish in two minutes.",
                    "We saved your progress.",
                    "Finish up", "#d98a16", "paid_conv", placement="banner",
                    data_used=[DataUse("abandoned step 3/4", FIRST_PARTY, ALLUDE, "resumes where they stopped")],
                    surface_note="allude"),
            Variant("C3", "Scarcity / urgency",
                    "Going fast on {brand} — save your spot.",
                    "Popular right now; the offer ends soon.",
                    "Get it now", "#8a5cf6", "lead_to_app", placement="cta",
                    data_used=[
                        DataUse("engagement score", FIRST_PARTY, ALLUDE, "raises CTA prominence"),
                        DataUse("low stock / end date", FIRST_PARTY, ALLUDE, "countdown"),
                    ],
                    surface_note="allude"),
            Variant("Cx", "Comparison-call-out (ungated)",
                    "We saw you comparing {brand} with two other sites.",
                    "Bought cross-site browsing says you're shopping around.",
                    "See the comparison", "#e0524a", "lead_to_app", blocked=True, placement="banner",
                    data_used=[DataUse("cross-site browsing (DMP)", BROKER, HOLD,
                                        "would recite competitor shopping — never shown")],
                    surface_note="HOLD — blocked by surface policy; the bandit cannot pull it"),
        ],
    ),
]

BY_ID = {s.id: s for s in SCENARIOS}


def scenario(sid: str) -> Scenario | None:
    return BY_ID.get((sid or "").strip().upper())


def gated_variants(s: Scenario) -> list[Variant]:
    return [v for v in s.variants if not v.blocked]


def blocked_variant(s: Scenario) -> Variant | None:
    return next((v for v in s.variants if v.blocked), None)


def find_variant(sid: str, vid: str) -> tuple[Scenario, Variant] | None:
    s = scenario(sid)
    if not s:
        return None
    v = next((x for x in s.variants if x.id == vid), None)
    return (s, v) if v else None


# --------------------------------------------------------------------------- #
# USE CASES — the four go-to-market shapes the same engine serves, each tied to
# the live scenario/surface that demonstrates it. Shown on /demo/live so a viewer
# can see how apt applies to a named customer, not just an abstract scenario.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class UseCase:
    customer: str                          # example customer / shape
    domain: str                            # their category
    title: str
    blurb: str
    signals: tuple[str, ...]               # the inputs apt uses
    maps_to: str                           # which scenario/surface backs it
    links: tuple[tuple[str, str], ...]     # (label, href) — page routes only


USE_CASES: tuple[UseCase, ...] = (
    UseCase(
        customer="gauntletai.com", domain="AI training",
        title="Anonymous visitor → personalized hero",
        blurb="A first-time visitor with no identity. apt resolves company, industry and region "
              "from the IP and rewrites the hero before it paints — every line carries a receipt. "
              "You're looking at it: change the IP above and the page follows.",
        signals=("reverse-IP company", "industry", "region", "daypart"),
        maps_to="Use case 1 · live demo site",
        links=(("Open the live demo", "/showcase/gauntletai"),)),
    UseCase(
        customer="skyfi.com", domain="satellite imagery",
        title="Geography is the product",
        blurb="For a geo-pinned business, apt detects the operator's region + sector and swaps the "
              "copy and a licensed backdrop to match — and refuses to pinpoint the exact asset "
              "(the creepiness ceiling). Pick a region + industry above to see it move.",
        signals=("region", "industry", "licensed imagery", "surface policy"),
        maps_to="Use case 2 · live demo site",
        links=(("Open the live demo", "/showcase/skyfi"),)),
    UseCase(
        customer="Known customer", domain="email / magic-link",
        title="Close the sale, provably",
        blurb="A known visitor gets a Gate-bounded persuasion play — authority, social proof, loss "
              "aversion, reciprocity — that surfaces only claims it can prove. Held claims are "
              "dropped. The receipt makes a bold closing claim safe to make.",
        signals=("CRM history", "on-site behaviour", "persuasion principle", "Gate-checked"),
        maps_to="Use case 3 · live demo site",
        links=(("Open the live demo", "/showcase/known"),)),
    UseCase(
        customer="Long-running A/B", domain="reinforcement learning",
        title="The bandit that can't win by lying",
        blurb="Over time the bandit learns which framing converts per segment from real clicks — and "
              "can only ever pull Gate-cleared arms, so it provably can't select a lie. Its lift is "
              "measured against a random control slice, not asserted.",
        signals=("Thompson sampling", "real clicks", "measured lift", "truth-bounded"),
        maps_to="Use case 4 · live demo site",
        links=(("Open the live demo", "/showcase/optimizer"),)),
)
