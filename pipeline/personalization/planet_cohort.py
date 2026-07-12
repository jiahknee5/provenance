"""The Planet seed cohort — 10 synthetic CUSTOMER personas, in the same REAL data shape
as pipeline.personalization.cohort (Vector · HubSpot · Clay three-source records).

Unlike the Gauntlet cohort (prospective students at @gauntletai.com), these are buyer-side
personas at fictional customer companies spanning Planet's nine market segments — an
agronomy director at a seed company, a cat-modeler at a reinsurer, a state forestry GIS
lead, a maritime-domain-awareness lead, a hydrology PhD. Login emails live at synthetic
customer-company domains so the work-email → company lane stays demonstrable.

Surface posture is identical to the reference cohort:
  Vector firmographics = `allude` · HubSpot form fields = `say` · HubSpot behavior =
  `allude` · Clay enrichment = `allude`/`hold` (modeled income never ships).

All values synthetic; no real PII; company names fictional. Spans all six UI archetypes.
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
    # Agriculture — the sample login persona (agronomy director, outcome-driven, warm MQL).
    {"id": "amara", "email": "amara.diallo@meridianagronomy.com",
     "vector": {"name": "Amara Diallo", "job_title": "Director of Digital Agronomy",
                "location": "Des Moines, IA", "company": "Meridian Agronomy",
                "org_type": "Agriculture Inputs", "company_size": "1001-5000",
                "visit_time": "06/18/2026 10:24 AM", "linkedin_url": "linkedin.com/in/amaradiallo"},
     "hubspot": {"submitted": True, "role": "Director of Agronomy", "phone": "515-555-0142",
                 "interest_reason": "monitor two million acres of seed production without adding agronomists",
                 "lifecycle": "mql", "lead_score": 62, "visits": 5, "source": "ad",
                 "top_pages": ["agriculture", "planetary-variables", "outcomes"], "past_customer": False},
     "clay": {"seniority": "senior", "tenure": 9, "technical": True, "industry": "Agriculture",
              "income_band": "$170–200K"}},

    # Insurance — cat modeler, ready + technical → fast_track.
    {"id": "tomas", "email": "tomas.eriksen@gulfstoneuw.com",
     "vector": {"name": "Tomas Eriksen", "job_title": "Lead Catastrophe Modeler", "location": "Hartford, CT",
                "company": "Gulfstone Underwriters", "org_type": "Insurance", "company_size": "5001-10000",
                "visit_time": "06/19/2026 9:40 AM", "linkedin_url": "linkedin.com/in/tomaseriksen"},
     "hubspot": {"submitted": True, "role": "Cat Modeler", "phone": "",
                 "interest_reason": "cut hurricane claims triage from weeks to days",
                 "lifecycle": "sql", "lead_score": 87, "visits": 8, "source": "ad",
                 "top_pages": ["insurance", "tasking", "pricing"], "past_customer": False},
     "clay": {"seniority": "ic", "tenure": 7, "technical": True, "industry": "Insurance",
              "income_band": "$150–180K"}},

    # Forestry & carbon — MRV lead, budget-anxious → cost_confident.
    {"id": "lena", "email": "lena.varga@northpinecarbon.com",
     "vector": {"name": "Lena Varga", "job_title": "MRV Program Lead", "location": "Portland, OR",
                "company": "Northpine Carbon", "org_type": "Environmental Services", "company_size": "51-200",
                "visit_time": "06/19/2026 2:15 PM", "linkedin_url": "linkedin.com/in/lenavarga"},
     "hubspot": {"submitted": True, "role": "MRV Lead", "phone": "",
                 "interest_reason": "afford carbon baselines that credit buyers actually believe",
                 "lifecycle": "mql", "lead_score": 58, "visits": 4, "source": "organic",
                 "top_pages": ["forest-carbon", "pricing", "financing"], "past_customer": False},
     "clay": {"seniority": "ic", "tenure": 5, "technical": True, "industry": "Carbon Markets",
              "income_band": "$95–115K"}},

    # Civil government — state forestry GIS lead, past crisis-program user → welcome_back.
    {"id": "diego", "email": "diego.reyes@jeffersonforestry.org",
     "vector": {"name": "Diego Reyes", "job_title": "GIS & Fire Analytics Lead", "location": "Sacramento, CA",
                "company": "Jefferson State Forestry", "org_type": "Government Administration",
                "company_size": "1001-5000",
                "visit_time": "06/19/2026 8:05 AM", "linkedin_url": "linkedin.com/in/diegoreyes"},
     "hubspot": {"submitted": True, "role": "GIS Lead", "phone": "",
                 "interest_reason": "digitize fire perimeters in minutes instead of helicopter hours",
                 "lifecycle": "customer", "lead_score": 74, "visits": 14, "source": "email",
                 "top_pages": ["civil-government", "disaster-data", "mosaics"], "past_customer": True},
     "clay": {"seniority": "ic", "tenure": 11, "technical": True, "industry": "Public Sector",
              "income_band": "$105–125K"}},

    # Education & research — hydrology PhD candidate, grant-constrained.
    {"id": "grace", "email": "grace.osei@cascadia.edu",
     "vector": {"name": "Grace Osei", "job_title": "PhD Candidate, Hydrology", "location": "Seattle, WA",
                "company": "Cascadia University", "org_type": "Higher Education", "company_size": "10000+",
                "visit_time": "06/19/2026 11:58 PM", "linkedin_url": "linkedin.com/in/graceosei"},
     "hubspot": {"submitted": True, "role": "Researcher", "phone": "",
                 "interest_reason": "get daily imagery for my flood time series without blowing my grant",
                 "lifecycle": "lead", "lead_score": 41, "visits": 3, "source": "ad",
                 "top_pages": ["education-research", "pricing", "insights-platform"], "past_customer": False},
     "clay": {"seniority": "new_grad", "tenure": 1, "technical": True, "industry": "Research",
              "income_band": "<$50K"}},

    # Energy & infrastructure — Vector-only: browsed once, never filled a form → explorer.
    {"id": "jules", "email": "jules.moreau@helioscorridor.com",
     "vector": {"name": "Jules Moreau", "job_title": "Pipeline Integrity Engineer", "location": "Houston, TX",
                "company": "Helios Corridor Energy", "org_type": "Oil & Energy", "company_size": "5001-10000",
                "visit_time": "06/19/2026 7:12 PM", "linkedin_url": "linkedin.com/in/julesmoreau"},
     "hubspot": {"submitted": False, "role": "", "interest_reason": "", "phone": "",
                 "lifecycle": "visitor", "lead_score": 11, "visits": 1, "source": "organic",
                 "top_pages": ["energy-infrastructure"], "past_customer": False},
     "clay": {"seniority": "ic", "tenure": 8, "technical": True, "industry": "Energy",
              "income_band": "$130–155K"}},

    # Maritime — MDA director at a coast-guard analytics contractor → prestige.
    {"id": "hanna", "email": "hanna.strand@nordwatchmda.com",
     "vector": {"name": "Hanna Strand", "job_title": "Director, Maritime Domain Awareness",
                "location": "Norfolk, VA", "company": "Nordwatch MDA",
                "org_type": "Defense & Space", "company_size": "201-500",
                "visit_time": "06/19/2026 1:33 PM", "linkedin_url": "linkedin.com/in/hannastrand"},
     "hubspot": {"submitted": True, "role": "Director", "phone": "",
                 "interest_reason": "bring dark-vessel detection to my enforcement team",
                 "lifecycle": "mql", "lead_score": 66, "visits": 4, "source": "referral",
                 "top_pages": ["maritime", "defense-intelligence", "vessel-detection"], "past_customer": False},
     "clay": {"seniority": "exec", "tenure": 13, "technical": True, "industry": "Maritime Security",
              "income_band": "$210K+"}},

    # Disaster response — humanitarian GIS coordinator; abandoned the trial signup.
    # The magic-token sample recipient (Liam-equivalent).
    {"id": "kofi", "email": "kofi.tanaka@pacificrelief.org",
     "vector": {"name": "Kofi Tanaka", "job_title": "GIS Coordinator, Emergency Response",
                "location": "Honolulu, HI", "company": "Pacific Relief Network",
                "org_type": "Non-profit Organization Management", "company_size": "201-500",
                "visit_time": "06/19/2026 10:48 AM", "linkedin_url": "linkedin.com/in/kofitanaka"},
     "hubspot": {"submitted": True, "role": "GIS Coordinator", "phone": "808-555-0199",
                 "interest_reason": "get before-and-after imagery to responders in the first 24 hours, fast",
                 "lifecycle": "sql", "lead_score": 89, "visits": 9, "source": "ad",
                 "top_pages": ["disaster-data", "sign-up", "insights-platform"], "past_customer": False,
                 "abandoned": "trial signup (step 2 of 3)"},
     "clay": {"seniority": "ic", "tenure": 6, "technical": True, "industry": "Humanitarian",
              "income_band": "$80–95K"}},

    # Financial services adjacency — Vector-only commodity-fund founder → prestige/explorer.
    {"id": "marta", "email": "marta.alvarez@terraquantfund.com",
     "vector": {"name": "Marta Alvarez", "job_title": "Founder & CIO", "location": "Miami, FL",
                "company": "TerraQuant Fund", "org_type": "Investment Management", "company_size": "11-50",
                "visit_time": "06/19/2026 8:22 PM", "linkedin_url": "linkedin.com/in/martaalvarez"},
     "hubspot": {"submitted": False, "role": "", "interest_reason": "", "phone": "",
                 "lifecycle": "visitor", "lead_score": 14, "visits": 1, "source": "organic",
                 "top_pages": ["insights-platform"], "past_customer": False},
     "clay": {"seniority": "exec", "tenure": 10, "technical": False, "industry": "Financial Services",
              "income_band": "$250K+"}},

    # Defense & intelligence — allied-government procurement lead → prestige.
    {"id": "viktor", "email": "viktor.novak@adriaticgeoint.com",
     "vector": {"name": "Viktor Novak", "job_title": "Head of GEOINT Procurement", "location": "Arlington, VA",
                "company": "Adriatic GeoInt Alliance", "org_type": "Defense & Space", "company_size": "1001-5000",
                "visit_time": "06/19/2026 3:48 PM", "linkedin_url": "linkedin.com/in/viktornovak"},
     "hubspot": {"submitted": True, "role": "Procurement Lead", "phone": "",
                 "interest_reason": "bring sovereign satellite capacity to my agency without building satellites",
                 "lifecycle": "mql", "lead_score": 71, "visits": 6, "source": "referral",
                 "top_pages": ["defense-intelligence", "satellite-services", "pelican"], "past_customer": False},
     "clay": {"seniority": "exec", "tenure": 15, "technical": False, "industry": "Defense",
              "income_band": "$230K+"}},
]


def magic_token(p: dict) -> str:
    """An opaque per-recipient token — the link we'd embed in an email we sent them.
    No PII in the URL; clicking it identifies them with no login or form."""
    return "pt_" + hashlib.sha256(f"planet-magic|{p['email']}".encode()).hexdigest()[:14]


BY_ID = {p["id"]: p for p in COHORT}
BY_EMAIL = {p["email"].lower(): p for p in COHORT}
BY_TOKEN = {magic_token(p): p for p in COHORT}


def match(email: str) -> dict | None:
    """Identify by email (typed at login) → the record we already hold."""
    return BY_EMAIL.get((email or "").strip().lower())


def by_token(token: str) -> dict | None:
    """Identify by magic-link token (clicked from an email) → the same record."""
    return BY_TOKEN.get((token or "").strip())


def view(p: dict) -> dict:
    """Normalize the three sources into the shape the segment/landing engine reads —
    identical contract to cohort.view() so segments.derive()/pick_archetype() reuse."""
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
        "declared": {"goal": hs.get("interest_reason", "") if submitted else ""},
        "deep": {"income_band": cl["income_band"], "device": "mobile" if "PM" in v["visit_time"] else "desktop",
                 "daypart": _daypart(v["visit_time"]),
                 "skills": cl.get("skills", []), "past_roles": cl.get("past_roles", []),
                 "education": cl.get("education", []), "interests": cl.get("interests", []),
                 "profiles": cl.get("profiles", []), "company_meta": cl.get("company_meta", "")},
        "_raw": p,
    }
