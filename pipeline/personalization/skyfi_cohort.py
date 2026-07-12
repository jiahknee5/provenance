"""The SkyFi seed cohort — 8 synthetic CUSTOMER personas, in the same REAL data shape
as pipeline.personalization.cohort (Vector · HubSpot · Clay three-source records).

Buyer-side personas at fictional customer companies spanning SkyFi's verticals
(docs/USE-CASES.md UC2): mining, precision-ag, construction/EPC, commercial real
estate/site selection, insurance cat-risk, energy/utilities, defense/gov. Login emails
live at synthetic customer-company domains so the work-email → company lane stays
demonstrable.

Two records carry SkyFi-specific first-party state:
  · ``sana`` has a **declared first-party AOI** (``hubspot.declared_aoi``) — she drew her
    own quarry boundary in the order flow. That declaration is the ONLY thing that flips
    the exact-AOI policy from ``hold`` to ``say`` (the S09 flip); the receipt then says
    "you told us" honestly.
  · ``ingrid`` is the defense/gov contact — **strict hold**: AOR/theater framing only,
    never a specific asset, regardless of tier or login.

Surface posture is identical to the reference cohorts:
  Vector firmographics = `allude` · HubSpot form fields = `say` · HubSpot behavior =
  `allude` · Clay enrichment = `allude`/`hold` (modeled income never ships).

All values synthetic; no real PII; company names fictional.
"""
from __future__ import annotations

import hashlib

CORE_SOURCES = ["vector", "hubspot", "clay"]


def _daypart(visit_time: str) -> str:
    """'06/19/2026 3:48 PM' → a coarse daypart (same rule as the reference cohort)."""
    try:
        hm, ap = visit_time.split()[-2:]
        h = int(hm.split(":")[0]) % 12 + (12 if ap.upper() == "PM" else 0)
    except Exception:
        h = 12
    return ("late night" if h >= 22 or h < 5 else "morning" if h < 12
            else "afternoon" if h < 17 else "evening")


COHORT: list[dict] = [
    # Mining — the AZ operator (S02's known-side analog): watch the pit without flying crews.
    {"id": "rhea", "email": "rhea.calder@copperlineresources.com",
     "vector": {"name": "Rhea Calder", "job_title": "Director of Mine Planning",
                "location": "Phoenix, AZ", "company": "Copperline Resources",
                "org_type": "Mining & Metals", "company_size": "1001-5000",
                "visit_time": "06/18/2026 9:12 AM", "linkedin_url": "linkedin.com/in/rheacalder"},
     "hubspot": {"submitted": True, "role": "Director of Mine Planning", "phone": "602-555-0117",
                 "interest_reason": "watch our pit and haul roads weekly without flying survey crews",
                 "lifecycle": "mql", "lead_score": 64, "visits": 5, "source": "ad",
                 "top_pages": ["mining", "tasking", "pricing"], "past_customer": False},
     "clay": {"seniority": "senior", "tenure": 12, "technical": True, "industry": "Mining",
              "income_band": "$180–210K"}},

    # Mining/aggregates — THE DECLARED-AOI PERSON (S09): she drew her own quarry boundary.
    {"id": "sana", "email": "sana.okafor@westbasinaggregates.com",
     "vector": {"name": "Sana Okafor", "job_title": "Operations Manager",
                "location": "Tucson, AZ", "company": "West Basin Aggregates",
                "org_type": "Mining & Metals", "company_size": "201-500",
                "visit_time": "06/19/2026 7:41 AM", "linkedin_url": "linkedin.com/in/sanaokafor"},
     "hubspot": {"submitted": True, "role": "Operations Manager", "phone": "",
                 "interest_reason": "keep an eye on our own quarry between site visits",
                 "lifecycle": "sql", "lead_score": 82, "visits": 7, "source": "organic",
                 "top_pages": ["existing-imagery", "pricing", "order"], "past_customer": False,
                 # First-party declaration — SHE drew this AOI in the order flow. This is
                 # the one and only basis on which exact-scale rendering is allowed (S09).
                 "declared_aoi": {"label": "West Basin quarry — Pima County, AZ",
                                  "scale": "site",
                                  "registered": "2026-06-02",
                                  "source": "AOI drawn in the SkyFi order flow"}},
     "clay": {"seniority": "senior", "tenure": 8, "technical": True, "industry": "Mining",
              "income_band": "$120–145K"}},

    # Construction/EPC — the known account (S06): sample login persona.
    {"id": "noor", "email": "noor.haddad@terrafirmepc.com",
     "vector": {"name": "Noor Haddad", "job_title": "VP Project Controls",
                "location": "Austin, TX", "company": "Terrafirm EPC",
                "org_type": "Construction", "company_size": "5001-10000",
                "visit_time": "06/19/2026 10:02 AM", "linkedin_url": "linkedin.com/in/noorhaddad"},
     "hubspot": {"submitted": True, "role": "VP Project Controls", "phone": "512-555-0163",
                 "interest_reason": "document build progress across 14 active sites monthly",
                 "lifecycle": "sql", "lead_score": 84, "visits": 9, "source": "email",
                 "top_pages": ["construction", "monitoring", "pricing"], "past_customer": False},
     "clay": {"seniority": "exec", "tenure": 14, "technical": False, "industry": "Construction",
              "income_band": "$220K+"}},

    # Defense/gov — the strict-hold contact (S07): AOR framing only, never a specific asset.
    {"id": "ingrid", "email": "ingrid.solheim@nordicaerodefence.com",
     "vector": {"name": "Ingrid Solheim", "job_title": "GEOINT Analysis Lead",
                "location": "Arlington, VA", "company": "Nordic Aero Defence",
                "org_type": "Defense & Space", "company_size": "1001-5000",
                "visit_time": "06/19/2026 1:27 PM", "linkedin_url": "linkedin.com/in/ingridsolheim"},
     "hubspot": {"submitted": True, "role": "GEOINT Analysis Lead", "phone": "",
                 "interest_reason": "add commercial tasking to our AOR coverage mix",
                 "lifecycle": "mql", "lead_score": 69, "visits": 4, "source": "referral",
                 "top_pages": ["defense", "sar", "tasking"], "past_customer": False},
     "clay": {"seniority": "exec", "tenure": 16, "technical": True, "industry": "Defense",
              "income_band": "$230K+"}},

    # Insurance cat-risk — returning known (S10).
    {"id": "priya", "email": "priya.raman@atlanticcatre.com",
     "vector": {"name": "Priya Raman", "job_title": "Catastrophe Risk Analyst",
                "location": "Hartford, CT", "company": "Atlantic Cat Re",
                "org_type": "Insurance", "company_size": "1001-5000",
                "visit_time": "06/19/2026 9:55 AM", "linkedin_url": "linkedin.com/in/priyaraman"},
     "hubspot": {"submitted": True, "role": "Cat Risk Analyst", "phone": "",
                 "interest_reason": "get before-and-after pairs for hurricane claims in days",
                 "lifecycle": "sql", "lead_score": 78, "visits": 6, "source": "ad",
                 "top_pages": ["insurance", "existing-imagery", "order"], "past_customer": False},
     "clay": {"seniority": "ic", "tenure": 7, "technical": True, "industry": "Insurance",
              "income_band": "$140–165K"}},

    # Precision ag — abandoned a tasking order mid-flow.
    {"id": "mateo", "email": "mateo.silva@rioverdeagro.com",
     "vector": {"name": "Mateo Silva", "job_title": "Agronomy Lead",
                "location": "Fresno, CA", "company": "Rio Verde Agro",
                "org_type": "Agriculture", "company_size": "201-500",
                "visit_time": "06/19/2026 6:48 PM", "linkedin_url": "linkedin.com/in/mateosilva"},
     "hubspot": {"submitted": True, "role": "Agronomy Lead", "phone": "",
                 "interest_reason": "check field condition mid-season without driving every block",
                 "lifecycle": "mql", "lead_score": 57, "visits": 5, "source": "ad",
                 "top_pages": ["agriculture", "order", "pricing"], "past_customer": False,
                 "abandoned": "tasking order (step 3 of 4)"},
     "clay": {"seniority": "ic", "tenure": 6, "technical": True, "industry": "Agriculture",
              "income_band": "$95–115K"}},

    # Commercial real estate / site selection — Vector-only explorer (never filled a form).
    {"id": "elena", "email": "elena.brooks@keystonesiteworks.com",
     "vector": {"name": "Elena Brooks", "job_title": "Site Selection Analyst",
                "location": "Denver, CO", "company": "Keystone Siteworks",
                "org_type": "Commercial Real Estate", "company_size": "51-200",
                "visit_time": "06/19/2026 8:19 PM", "linkedin_url": "linkedin.com/in/elenabrooks"},
     "hubspot": {"submitted": False, "role": "", "interest_reason": "", "phone": "",
                 "lifecycle": "visitor", "lead_score": 12, "visits": 1, "source": "organic",
                 "top_pages": ["existing-imagery"], "past_customer": False},
     "clay": {"seniority": "ic", "tenure": 4, "technical": False, "industry": "Real Estate",
              "income_band": "$85–105K"}},

    # Energy/utilities — ROW integrity engineer, past customer → welcome_back.
    {"id": "dmitri", "email": "dmitri.volkov@meridiangridworks.com",
     "vector": {"name": "Dmitri Volkov", "job_title": "ROW Integrity Engineer",
                "location": "Houston, TX", "company": "Meridian Gridworks",
                "org_type": "Utilities", "company_size": "5001-10000",
                "visit_time": "06/19/2026 11:05 AM", "linkedin_url": "linkedin.com/in/dmitrivolkov"},
     "hubspot": {"submitted": True, "role": "ROW Integrity Engineer", "phone": "",
                 "interest_reason": "check corridor encroachment quarterly from the archive",
                 "lifecycle": "customer", "lead_score": 72, "visits": 12, "source": "email",
                 "top_pages": ["energy", "existing-imagery", "monitoring"], "past_customer": True},
     "clay": {"seniority": "ic", "tenure": 10, "technical": True, "industry": "Energy",
              "income_band": "$135–160K"}},
]


def magic_token(p: dict) -> str:
    """An opaque per-recipient token — the link we'd embed in an email we sent them.
    No PII in the URL; clicking it identifies them with no login or form."""
    return "sk_" + hashlib.sha256(f"skyfi-magic|{p['email']}".encode()).hexdigest()[:14]


BY_ID = {p["id"]: p for p in COHORT}
BY_EMAIL = {p["email"].lower(): p for p in COHORT}
BY_TOKEN = {magic_token(p): p for p in COHORT}


def match(email: str) -> dict | None:
    """Identify by email (typed at login) → the record we already hold."""
    return BY_EMAIL.get((email or "").strip().lower())


def by_token(token: str) -> dict | None:
    """Identify by magic-link token (clicked from an email) → the same record."""
    return BY_TOKEN.get((token or "").strip())


def declared_aoi(p: dict | None) -> dict | None:
    """The person's declared first-party AOI, if they registered one (the S09 basis)."""
    if not p:
        return None
    aoi = (p.get("hubspot") or {}).get("declared_aoi")
    return dict(aoi) if aoi else None


def view(p: dict) -> dict:
    """Normalize the three sources into the shape the segment/landing engine reads —
    identical contract to cohort.view() so segments.derive()/pick_archetype() reuse.
    SkyFi addition: declared.aoi carries the first-party AOI (say-level, S09 flip)."""
    v, hs, cl = p["vector"], p["hubspot"], p["clay"]
    submitted = hs.get("submitted", False)
    return {
        "id": p["id"], "email": p["email"], "name": v["name"], "submitted": submitted,
        "linkedin": {"title": v["job_title"], "company": v["company"], "industry": cl["industry"],
                     "seniority": cl["seniority"], "tenure": cl["tenure"], "technical": cl["technical"],
                     "location": v["location"], "headline": v["job_title"]},
        "hubspot": {"lifecycle": hs["lifecycle"], "lead_score": hs["lead_score"], "visits": hs["visits"],
                    "top_pages": hs["top_pages"], "source": hs["source"],
                    "past_customer": hs["past_customer"], "abandoned": hs.get("abandoned")},
        "declared": {"goal": hs.get("interest_reason", "") if submitted else "",
                     "aoi": declared_aoi(p)},
        "deep": {"income_band": cl["income_band"], "device": "mobile" if "PM" in v["visit_time"] else "desktop",
                 "daypart": _daypart(v["visit_time"]),
                 "skills": cl.get("skills", []), "past_roles": cl.get("past_roles", []),
                 "education": cl.get("education", []), "interests": cl.get("interests", []),
                 "profiles": cl.get("profiles", []), "company_meta": cl.get("company_meta", "")},
        "_raw": p,
    }
