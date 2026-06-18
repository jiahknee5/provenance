"""The enrichment data catalog — every source we *could* enrich with, paid or free.

This is reference data for the /enrichment-catalog page. It is honest about cost and the
lawful-basis question per source. `used_in_demo` flags which ones the demo actually wires
(as simulated connectors, except the one live free connector — see config.enrich_live()).
Nothing here calls a paid API; the paid rows are documented, not invoked.
"""
from __future__ import annotations

# stage: where in the touchpoint flow the source applies
FREE = "free"
PAID = "paid"
ENGAGEMENT = "engagement"

CATALOG = [
    # --- free / low-cost (form -> email) ---
    {"name": "Email domain parse", "stage": FREE, "gives": "company domain, B2B vs personal",
     "cost": "$0", "basis": "user-provided (low risk)", "freshness": "instant",
     "source_id": "email_domain", "used_in_demo": True, "live": True},
    {"name": "DNS / MX / WHOIS", "stage": FREE, "gives": "mail provider, domain age, registrar",
     "cost": "$0", "basis": "public record", "freshness": "days",
     "source_id": "dns_mx", "used_in_demo": True, "live": True},
    {"name": "Company website scrape", "stage": FREE, "gives": "products, locations, tech hints",
     "cost": "$0", "basis": "ToS varies; respect robots.txt", "freshness": "weeks",
     "source_id": None, "used_in_demo": False, "live": False},
    {"name": "News / RSS / Google News", "stage": FREE, "gives": "recent events, funding, initiatives",
     "cost": "$0", "basis": "public; attribute the source", "freshness": "hours",
     "source_id": "company_news_rss", "used_in_demo": True, "live": True},
    {"name": "SEC EDGAR", "stage": FREE, "gives": "revenue, risk factors (public cos)",
     "cost": "$0", "basis": "public record", "freshness": "quarterly",
     "source_id": None, "used_in_demo": False, "live": False},
    {"name": "GitHub / job boards", "stage": FREE, "gives": "tech stack, hiring signals",
     "cost": "$0", "basis": "public; ToS", "freshness": "days",
     "source_id": None, "used_in_demo": False, "live": False},
    {"name": "LinkedIn public profile", "stage": FREE, "gives": "title, seniority",
     "cost": "$0", "basis": "ToS-restricted — careful", "freshness": "weeks",
     "source_id": None, "used_in_demo": False, "live": False},
    {"name": "BuiltWith (free tier)", "stage": FREE, "gives": "website tech stack",
     "cost": "free tier", "basis": "vendor ToS", "freshness": "weeks",
     "source_id": None, "used_in_demo": False, "live": False},

    # --- paid (form -> email, and return-visit refresh) ---
    {"name": "Clearbit / HubSpot Enrichment", "stage": PAID, "gives": "firmographics, role, seniority",
     "cost": "per-enrichment / seat", "basis": "vendor AUP + your basis", "freshness": "weeks",
     "source_id": "firmographic_sim", "used_in_demo": True, "live": False},
    {"name": "ZoomInfo", "stage": PAID, "gives": "contact + company, org chart",
     "cost": "seat + credits ($$$)", "basis": "AUP is strict; record basis", "freshness": "weeks",
     "source_id": "firmographic_sim", "used_in_demo": False, "live": False},
    {"name": "Apollo.io", "stage": PAID, "gives": "contact + intent", "cost": "seat + credits",
     "basis": "AUP", "freshness": "weeks", "source_id": None, "used_in_demo": False, "live": False},
    {"name": "People Data Labs", "stage": PAID, "gives": "person/company graph", "cost": "per-record API",
     "basis": "basis required", "freshness": "weeks", "source_id": None, "used_in_demo": False, "live": False},
    {"name": "Cognism / Lusha", "stage": PAID, "gives": "EU-compliant B2B contacts", "cost": "seat + credits",
     "basis": "GDPR-positioned", "freshness": "weeks", "source_id": None, "used_in_demo": False, "live": False},
    {"name": "6sense / Demandbase", "stage": PAID, "gives": "account intent, buying stage",
     "cost": "platform ($$$$)", "basis": "account-level, lower PII risk", "freshness": "days",
     "source_id": "intent_sim", "used_in_demo": True, "live": False},
    {"name": "Bombora", "stage": PAID, "gives": "topic surge / intent", "cost": "subscription",
     "basis": "account-level", "freshness": "weekly", "source_id": "intent_sim", "used_in_demo": False, "live": False},

    # --- engagement (email sent -> click -> website) ---
    {"name": "Email open pixel", "stage": ENGAGEMENT, "gives": "opened? when? client?",
     "cost": "$0", "basis": "disclose tracking; some clients block", "freshness": "realtime",
     "source_id": None, "used_in_demo": True, "live": False},
    {"name": "Click tracking (wrapped links)", "stage": ENGAGEMENT, "gives": "which CTA, when",
     "cost": "$0", "basis": "first-party, low risk", "freshness": "realtime",
     "source_id": None, "used_in_demo": True, "live": False},
    {"name": "First-party site analytics", "stage": ENGAGEMENT, "gives": "pages, dwell, return",
     "cost": "$0", "basis": "first-party cookie + notice", "freshness": "realtime",
     "source_id": None, "used_in_demo": True, "live": False},
    {"name": "Reverse-IP (Clearbit Reveal / KickFire)", "stage": ENGAGEMENT, "gives": "company of an anonymous visit",
     "cost": "per-lookup", "basis": "account-level, no PII", "freshness": "realtime",
     "source_id": None, "used_in_demo": False, "live": False},
]


def grouped() -> dict:
    out = {FREE: [], PAID: [], ENGAGEMENT: []}
    for row in CATALOG:
        out[row["stage"]].append(row)
    return out
