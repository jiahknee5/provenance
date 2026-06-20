"""The seed cohort — 10 example users, in our REAL data shape.

Three core sources (others in the catalog are greyed out):
  • Vector   — de-anonymized traffic. For every visitor (even anonymous, no form) we may get
               name, job title, location, company, org type, company size, visit time, LinkedIn URL.
  • HubSpot  — form submissions + CRM. Custom fields (name, email, phone, role, interest reason)
               passed client-side, plus lifecycle / lead score / page behavior. Only if they submitted.
  • Clay     — the enricher: waterfalls from Vector/HubSpot inputs to append more (seniority,
               tenure, technical depth, industry, modeled income…).

Surface posture (the anti-creepiness control, per source):
  Vector firmographics = `allude` (we de-anonymized it — they didn't tell us → shape, don't recite).
  HubSpot form fields  = `say` (they typed it). HubSpot behavior = `allude`. Clay = `allude`/`hold`.
  The login email (entered at the QR) is declared → name/email may be `say`.

Some users are **Vector-only** (de-anon'd, never submitted a form) — to show the de-anon power.
All values synthetic; no real PII. Designed to span all six UI archetypes.
"""
from __future__ import annotations

import hashlib

CORE_SOURCES = ["vector", "hubspot", "clay"]


def _daypart(visit_time: str) -> str:
    """'06/19/2026 3:48 PM' → a coarse daypart for the channel segment + dark/light mode."""
    try:
        hm, ap = visit_time.split()[-2:]
        h = int(hm.split(":")[0]) % 12 + (12 if ap.upper() == "PM" else 0)
    except Exception:
        h = 12
    return ("late night" if h >= 22 or h < 5 else "morning" if h < 12
            else "afternoon" if h < 17 else "evening")


COHORT: list[dict] = [
    # Vector-only (the example from the brief): de-anon'd, never filled a form.
    {"id": "allen", "email": "allen.green@gauntletai.com",
     "vector": {"name": "Allen Green", "job_title": "Graphic Designer | Engineering and Research",
                "location": "Charlotte, NC", "company": "Sierra Club",
                "org_type": "Non-profit Organization Management", "company_size": "501-1000",
                "visit_time": "06/19/2026 3:48 PM", "linkedin_url": "linkedin.com/in/allengreen"},
     "hubspot": {"submitted": False, "role": "", "interest_reason": "", "phone": "",
                 "lifecycle": "visitor", "lead_score": 8, "visits": 1, "top_pages": ["home"],
                 "source": "organic", "past_customer": False},
     "clay": {"seniority": "ic", "tenure": 6, "technical": False, "industry": "Non-profit",
              "income_band": "$70–90K"}},

    {"id": "maya", "email": "maya.chen@gauntletai.com",
     "vector": {"name": "Maya Chen", "job_title": "QA Engineer", "location": "Austin, TX",
                "company": "Cedar Health", "org_type": "Hospital & Health Care",
                "company_size": "1001-5000", "visit_time": "06/18/2026 11:24 PM",
                "linkedin_url": "linkedin.com/in/mayachen"},
     "hubspot": {"submitted": True, "role": "QA Engineer", "phone": "512-555-0142",
                 "interest_reason": "switch into AI without going broke",
                 "lifecycle": "mql", "lead_score": 58, "visits": 4, "source": "ad",
                 "top_pages": ["night-cohort", "pricing", "financing"], "past_customer": False},
     "clay": {"seniority": "ic", "tenure": 3, "technical": True, "industry": "Healthcare IT",
              "income_band": "$95–115K"}},

    {"id": "darnell", "email": "darnell.brooks@gauntletai.com",
     "vector": {"name": "Darnell Brooks", "job_title": "Senior Product Manager", "location": "Chicago, IL",
                "company": "Northwind", "org_type": "Computer Software", "company_size": "201-500",
                "visit_time": "06/19/2026 10:05 AM", "linkedin_url": "linkedin.com/in/darnellbrooks"},
     "hubspot": {"submitted": True, "role": "Product Manager", "phone": "",
                 "interest_reason": "lead AI products, not just manage them",
                 "lifecycle": "sql", "lead_score": 86, "visits": 7, "source": "referral",
                 "top_pages": ["curriculum", "apply", "outcomes"], "past_customer": False},
     "clay": {"seniority": "senior", "tenure": 8, "technical": False, "industry": "SaaS",
              "income_band": "$160–190K"}},

    {"id": "priya", "email": "priya.nair@gauntletai.com",
     "vector": {"name": "Priya Nair", "job_title": "Software Engineer (new grad)", "location": "Remote",
                "company": "—", "org_type": "—", "company_size": "—",
                "visit_time": "06/19/2026 7:12 PM", "linkedin_url": "linkedin.com/in/priyanair"},
     "hubspot": {"submitted": True, "role": "Student", "phone": "",
                 "interest_reason": "get my first job in AI",
                 "lifecycle": "lead", "lead_score": 30, "visits": 2, "source": "ad",
                 "top_pages": ["outcomes", "home"], "past_customer": False},
     "clay": {"seniority": "new_grad", "tenure": 0, "technical": True, "industry": "Tech",
              "income_band": "<$50K"}},

    {"id": "tom", "email": "tom.riley@gauntletai.com",
     "vector": {"name": "Tom Riley", "job_title": "Backend Engineer", "location": "Denver, CO",
                "company": "Lumen", "org_type": "Financial Services", "company_size": "5001-10000",
                "visit_time": "06/19/2026 9:40 AM", "linkedin_url": "linkedin.com/in/tomriley"},
     "hubspot": {"submitted": True, "role": "Engineer", "phone": "",
                 "interest_reason": "go deeper after Intro to Python",
                 "lifecycle": "customer", "lead_score": 70, "visits": 12, "source": "email",
                 "top_pages": ["advanced-track", "alumni"], "past_customer": True},
     "clay": {"seniority": "ic", "tenure": 5, "technical": True, "industry": "Fintech",
              "income_band": "$120–140K"}},

    {"id": "elena", "email": "elena.vasquez@gauntletai.com",
     "vector": {"name": "Elena Vasquez", "job_title": "Director of Engineering", "location": "New York, NY",
                "company": "Atlas Bank", "org_type": "Banking", "company_size": "10000+",
                "visit_time": "06/19/2026 2:15 PM", "linkedin_url": "linkedin.com/in/elenavasquez"},
     "hubspot": {"submitted": True, "role": "Director", "phone": "",
                 "interest_reason": "bring AI capability to my engineering team",
                 "lifecycle": "mql", "lead_score": 64, "visits": 3, "source": "organic",
                 "top_pages": ["enterprise", "instructors"], "past_customer": False},
     "clay": {"seniority": "exec", "tenure": 12, "technical": True, "industry": "Banking",
              "income_band": "$240K+"}},

    {"id": "sam", "email": "sam.okafor@gauntletai.com",
     "vector": {"name": "Sam Okafor", "job_title": "Barista", "location": "Phoenix, AZ",
                "company": "Local Coffee Co", "org_type": "Food & Beverages", "company_size": "11-50",
                "visit_time": "06/18/2026 11:58 PM", "linkedin_url": "linkedin.com/in/samokafor"},
     "hubspot": {"submitted": True, "role": "Career changer", "phone": "",
                 "interest_reason": "afford a real career change",
                 "lifecycle": "lead", "lead_score": 41, "visits": 3, "source": "ad",
                 "top_pages": ["financing", "scholarships", "pricing"], "past_customer": False},
     "clay": {"seniority": "career_change", "tenure": 0, "technical": False, "industry": "Service",
              "income_band": "<$50K"}},

    {"id": "grace", "email": "grace.liu@gauntletai.com",
     "vector": {"name": "Grace Liu", "job_title": "Data Analyst", "location": "Seattle, WA",
                "company": "Meadow Retail", "org_type": "Retail", "company_size": "1001-5000",
                "visit_time": "06/19/2026 6:30 PM", "linkedin_url": "linkedin.com/in/graceliu"},
     "hubspot": {"submitted": True, "role": "Analyst", "phone": "",
                 "interest_reason": "move from analytics into ML engineering and roughly double my salary",
                 "lifecycle": "mql", "lead_score": 60, "visits": 5, "source": "referral",
                 "top_pages": ["outcomes", "salary-report", "curriculum"], "past_customer": False},
     "clay": {"seniority": "ic", "tenure": 4, "technical": True, "industry": "Retail",
              "income_band": "$85–100K"}},

    # Vector-only: a founder who browsed once and bounced — we still know exactly who he is.
    {"id": "marcus", "email": "marcus.webb@gauntletai.com",
     "vector": {"name": "Marcus Webb", "job_title": "Founder", "location": "Miami, FL",
                "company": "Webb Studio", "org_type": "Marketing & Advertising", "company_size": "11-50",
                "visit_time": "06/19/2026 8:22 PM", "linkedin_url": "linkedin.com/in/marcuswebb"},
     "hubspot": {"submitted": False, "role": "", "interest_reason": "", "phone": "",
                 "lifecycle": "visitor", "lead_score": 12, "visits": 1, "source": "organic",
                 "top_pages": ["home"], "past_customer": False},
     "clay": {"seniority": "exec", "tenure": 9, "technical": False, "industry": "Agency",
              "income_band": "$200K+"}},

    {"id": "liam", "email": "liam.foster@gauntletai.com",
     "vector": {"name": "Liam Foster", "job_title": "Full-stack Engineer", "location": "Portland, OR",
                "company": "Pinecrest", "org_type": "Computer Software", "company_size": "51-200",
                "visit_time": "06/19/2026 10:48 AM", "linkedin_url": "linkedin.com/in/liamfoster"},
     "hubspot": {"submitted": True, "role": "Engineer", "phone": "503-555-0199",
                 "interest_reason": "go from web dev to AI engineer, fast",
                 "lifecycle": "sql", "lead_score": 91, "visits": 9, "source": "ad",
                 "top_pages": ["apply", "curriculum", "start-dates"], "past_customer": False,
                 "abandoned": "application (step 3 of 4)"},
     "clay": {"seniority": "ic", "tenure": 4, "technical": True, "industry": "SaaS",
              "income_band": "$110–130K"}},

    # The operator's own record — REAL data, fetched 2026-06-20 from People Data Labs via the
    # confirmed LinkedIn (his Gmail had NO PDL match; the realistic path is Vector de-anon →
    # LinkedIn URL → PDL enrich). vector firmographics + clay industry/tenure are REAL; he never
    # filled a HubSpot form (submitted=False); PDL's free tier redacts personal location + income,
    # so those are left empty rather than fabricated. (linkedin→enrich lives in realenrich._pdl.)
    {"id": "johnny", "email": "johnny.c.chung@gmail.com",
     "vector": {"name": "Johnny Chung", "job_title": "VP, Climate Scenario Leader", "location": "",
                "company": "U.S. Bank", "org_type": "Banking", "company_size": "10001+",
                "visit_time": "06/20/2026 9:15 AM", "linkedin_url": "linkedin.com/in/johnnycchung"},
     "hubspot": {"submitted": False, "role": "", "phone": "", "interest_reason": "",
                 "lifecycle": "lead", "lead_score": 0, "visits": 1, "source": "vector_deanon",
                 "top_pages": [], "past_customer": False},
     "clay": {"seniority": "exec", "tenure": 2, "technical": True, "industry": "Banking",
              "income_band": "",
              # deeper REAL layers from PDL (employment history, education, skills, interests, social)
              "skills": ["artificial intelligence", "agents", "climate risk assessment", "analytics"],
              "past_roles": ["VP, Climate Risk Analytics — MUFG (2018–24)",
                             "Director, Data & Analytics — Havas Media (2015–18)"],
              "education": ["Georgetown (McDonough MBA)", "Frankfurt School of Finance"],
              "interests": ["clean technology", "golf", "healthcare"],
              "profiles": ["LinkedIn", "Facebook"],
              "company_meta": "U.S. Bank · est. 1863 · Minneapolis HQ · 10,001+ employees"}},
]

def magic_token(p: dict) -> str:
    """An opaque per-recipient token — the link we'd embed in an email we sent them.
    No PII in the URL; clicking it identifies them with no login or form."""
    return "mt_" + hashlib.sha256(f"magic|{p['email']}".encode()).hexdigest()[:14]


BY_ID = {p["id"]: p for p in COHORT}
BY_EMAIL = {p["email"].lower(): p for p in COHORT}
BY_TOKEN = {magic_token(p): p for p in COHORT}


def match(email: str) -> dict | None:
    """Identify by email (typed, or verified via Google) → the record we already hold."""
    return BY_EMAIL.get((email or "").strip().lower())


def by_token(token: str) -> dict | None:
    """Identify by magic-link token (clicked from an email) → the same record."""
    return BY_TOKEN.get((token or "").strip())


def view(p: dict) -> dict:
    """Normalize the three real sources into the shape the segment/landing engine reads,
    keeping the raw sources attached for source-accurate explanation."""
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
