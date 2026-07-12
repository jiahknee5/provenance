"""What "Sign in with Google" actually gives you — organized into honest tiers.

The demo's point: a Google login does NOT hand over "everything Google knows." It returns
the scopes you consent to. So every data point here is tagged with its TRUE availability:

  granted     — returned by the basic OAuth profile/email scopes the instant you tap Allow.
  extra_scope — a separate OAuth scope on the same consent screen (you approve it, usually
                without reading): calendar, contacts, Gmail metadata, Drive, YouTube, Fit.
  not_api     — Google HAS it and uses it (ads), but exposes NO API to hand it to an app:
                ad-interest profile, search history, location timeline, age/demographics.
  bought      — NOT from your Google login at all. Inferred or purchased from a data broker,
                keyed off the email your login just verified. This is the real "ultra" tier.

Values are synthetic (one persona). Real OAuth, when configured, fills the `granted` tier
with the actual signed-in profile; everything below stays illustrative + labeled.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from pipeline.personalization import realenrich

GRANTED = "granted"
EXTRA_SCOPE = "extra_scope"
NOT_API = "not_api"
BOUGHT = "bought"

TIERS = [
    {"id": GRANTED, "n": 0, "label": "What your login actually handed us",
     "blurb": "Returned by the basic profile + email scopes the instant you tapped “Allow.” "
              "This is the whole of what a plain Google login gives.",
     "how": "OAuth scopes: openid · email · profile", "tone": "ok"},
    {"id": EXTRA_SCOPE, "n": 1, "label": "One more checkbox",
     "blurb": "Each of these is a separate scope on the SAME consent screen. Most people tap "
              "through without reading — and hand over far more than their profile.",
     "how": "Additional OAuth scopes (calendar.readonly, contacts.readonly, gmail.metadata, …)",
     "tone": "warn"},
    {"id": NOT_API, "n": 2, "label": "Google has it — but won't give it to an app",
     "blurb": "Google collects and monetizes these, but exposes NO API that returns them to a "
              "third party. We can’t get them from your login — only infer or buy them.",
     "how": "No OAuth scope exists. (Maps Timeline API was shut down; ad/search profiles are internal.)",
     "tone": "info"},
    {"id": BOUGHT, "n": 3, "label": "Bought / inferred — the real “ultra-personalized” tier",
     "blurb": "This is where “we know everything” actually comes from: a data-broker append "
              "matched to the email your Google login just verified. Not your Google data — purchased.",
     "how": "Broker append (Acxiom / Experian / Epsilon), keyed on your verified email",
     "tone": "bad"},
]
TIER_BY_ID = {t["id"]: t for t in TIERS}


@dataclass(frozen=True)
class Item:
    label: str
    value: str
    avail: str          # granted | extra_scope | not_api | bought
    how: str            # the concrete way you'd actually obtain it
    creepiness: int     # 1..5
    scope: str = ""     # the OAuth scope, where applicable


NOTE_REAL = ("The top tier is REAL — fetched live for this email just now (domain, account type, "
             "and a public Gravatar profile IF one exists). Everything below is ILLUSTRATIVE: the "
             "KIND of data each source exposes — not a real lookup on this person.")
NOTE_DEMO = ("Sign in with Google, or open ?email=you@domain — the top tier fills with REAL data "
             "fetched for that address. The lower tiers stay illustrative (categories, not a lookup).")

# Tier 0 (GRANTED) is built at runtime from the real email — see _granted()/overview(). The lists
# below are the illustrative lower tiers: what each source WOULD expose, framed as categories.
ITEMS: list[Item] = [
    # ---- TIER 1 · EXTRA_SCOPE — one more checkbox ----
    Item("Calendar", "‘OB checkup Thu 2pm’, ‘daycare tour Sat’", EXTRA_SCOPE,
         "calendar.readonly — your events, titles included.", 5, "calendar.readonly"),
    Item("Contacts", "1,840 contacts: partner ‘Jordan’, mom, an OB-GYN", EXTRA_SCOPE,
         "contacts.readonly — your whole address book, with labels.", 4, "contacts.readonly"),
    Item("Gmail metadata", "receipts from Pampers, BuyBuyBaby, a fertility clinic", EXTRA_SCOPE,
         "gmail.metadata — senders + subjects reveal purchases without reading bodies.", 5, "gmail.metadata"),
    Item("Drive file list", "‘Q3_budget.xlsx’, ‘offer_letter.pdf’, ‘custody_notes.docx’", EXTRA_SCOPE,
         "drive.metadata.readonly — file names, no contents needed.", 5, "drive.metadata.readonly"),
    Item("YouTube history", "‘newborn sleep’, ‘career switch at 34’", EXTRA_SCOPE,
         "youtube.readonly — watch + search history as interests.", 4, "youtube.readonly"),
    Item("Fitness", "avg 6,200 steps, resting HR 64", EXTRA_SCOPE,
         "fitness.activity.read — steps, heart rate, workouts.", 4, "fitness.activity.read"),

    # ---- TIER 2 · NOT_API — Google has it, no API gives it ----
    Item("Ad-interest profile", "‘new parents’, ‘career change’, ‘home improvement’", NOT_API,
         "Google’s ‘My Ad Center’ shows it to YOU; there is no API to hand it to an app.", 4),
    Item("Search history", "(what you’ve Googled)", NOT_API,
         "Stored in your account, shown to you — never exposed to a third party via OAuth.", 5),
    Item("Location timeline", "home, work, 2 hospital visits this month", NOT_API,
         "Maps Timeline. The API that returned this was SHUT DOWN; it’s on-device only now.", 5),
    Item("Age / birthdate", "(Google may have it)", NOT_API,
         "Only via the restricted ‘birthday’ scope, IF you set it visible AND the app is verified. "
         "Otherwise it is inferred or bought — see below.", 3),
    Item("Modeled demographics", "(Google’s internal ad model)", NOT_API,
         "Google models age/income/household for ad targeting — internal, never handed out.", 4),

    # ---- TIER 3 · BOUGHT — the real "ultra" tier, keyed off the verified email ----
    Item("Age", "34", BOUGHT, "Broker append on the email — not from Google.", 3),
    Item("Household income", "modeled $115–135K", BOUGHT, "Experian/Acxiom income model.", 4),
    Item("Home & net worth", "owns a ~$540K home · net worth $250–500K", BOUGHT, "Property records + wealth model.", 4),
    Item("Life events", "‘new parent (0–6mo)’, ‘recently separated’", BOUGHT, "Epsilon life-event triggers — the most sensitive, most traded.", 5),
    Item("Vehicle", "2021 Subaru Outback", BOUGHT, "Polk / Oracle auto registration data.", 3),
    Item("Political & health audiences", "likely-Democrat donor · ‘new parent’, ‘allergy’ audiences", BOUGHT,
         "Voter file + health-adjacent ad audiences — protected/sensitive.", 5),
    Item("Cross-device & offline", "this phone + work laptop + home iPad · Target loyalty: diapers weekly", BOUGHT,
         "Identity graph (LiveRamp) + resold retail loyalty data.", 5),
]

ITEMS_BY_TIER = {t["id"]: [i for i in ITEMS if i.avail == t["id"]] for t in TIERS}


BASIC_LABELS = {"Email domain", "Account type", "Public profile (Gravatar)"}


def _granted(email: str, profile: dict | None, real: dict | None) -> list[dict]:
    """Tier 0, built from REAL data: realenrich for the email + (if present) a real OAuth profile.

    Each row is tagged real=True only when the value was actually fetched/returned — placeholders
    ("filled by a real Google sign-in") are real=False so the UI never overclaims.
    """
    rows: list[dict] = []

    def row(label, value, how, real, scope="", creep=1):
        rows.append({"label": label, "value": value, "avail": GRANTED, "how": how,
                     "creepiness": creep, "scope": scope, "real": real})

    row("Email (verified)", email or "—", "email scope returns the verified address.", bool(email), "email")
    rmap = {r["label"]: r for r in (real["real"] if real else [])}
    for lbl in ("Email domain", "Account type", "Public profile (Gravatar)"):
        r = rmap.get(lbl)
        row(lbl, r["value"] if r else "—", (r["source"] + " — REAL, fetched live") if r else "—",
            bool(r and r["real"]))
    if profile:   # an actual Google OAuth sign-in happened
        row("Profile name & photo", f"{profile.get('name', '')}"
            + (" · photo ✓" if profile.get("picture") else ""),
            "profile scope returns name + photo — REAL.", True, "profile")
        row("Google account ID (sub)", str(profile.get("sub", "—")),
            "stable OpenID subject — your permanent key here — REAL.", True, "openid", 2)
    else:
        row("Profile name & photo", "(filled by a real Google sign-in)",
            "profile scope returns name + photo.", False, "profile")
        row("Google account ID (sub)", "(filled by a real Google sign-in)",
            "the stable OpenID subject — your permanent key here.", False, "openid", 2)
    return rows


def overview(email: str = "", profile: dict | None = None) -> dict:
    email = (email or "").strip().lower()
    real = realenrich.enrich(email) if email else None
    granted = _granted(email, profile, real)
    items_by_tier = {GRANTED: granted,
                     **{t: [i.__dict__ for i in ITEMS_BY_TIER[t]] for t in (EXTRA_SCOPE, NOT_API, BOUGHT)}}
    counts = {k: len(v) for k, v in items_by_tier.items()}
    persona = {"name": email or "Guest", "email": email or "(not signed in)",
               "real": bool(email), "note": NOTE_REAL if email else NOTE_DEMO}
    # Real rows fetched beyond the login basics (People Data Labs person data, company news, …).
    real_extra = [r for r in (real["real"] if real else []) if r["real"] and r["label"] not in BASIC_LABELS]
    return {
        "persona": persona, "tiers": TIERS, "items_by_tier": items_by_tier,
        "counts": counts, "total": sum(counts.values()),
        "granted": counts[GRANTED], "not_login": counts[NOT_API] + counts[BOUGHT],
        "real_have": sum(1 for r in granted if r["real"]),
        "real_extra": real_extra, "pdl_on": bool(os.environ.get("PDL_API_KEY", "").strip()),
    }
