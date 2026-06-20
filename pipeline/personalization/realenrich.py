"""Real enrichment — fetch only what's GENUINELY available for an email, right now, free.

No synthetic personas. For a given email we attempt the actually-free, real sources:
  • domain parse         — personal vs corporate (instant, no network)
  • DNS resolve / provider— does the domain resolve; mail provider hint
  • Gravatar             — public profile (name, location, photo, linked accounts) IF the
                           person set one up — keyed on the email hash (free)
  • company news         — for a corporate domain, a real public-news headline (live RSS)

Everything else (name, title, company, age, income, …) is HONESTLY marked as not available
from the email alone — it requires the operator's own Vector / HubSpot / Clay (load an
export), a real Google sign-in, or a paid data broker. We never fabricate a value.

Network calls are cached (LLMCache) so a re-run is deterministic. Default mode is `live`
(it only hits free, public, no-PII-leaking endpoints); pass mode="off" to skip the network.
"""
from __future__ import annotations

import hashlib
import os

from pipeline.common import config
from pipeline.common.cache import LLMCache

# People Data Labs — a REAL synchronous "email → person" enrichment API (free tier ~100/mo).
# This is the kind of endpoint Clay is NOT: POST/GET an email, get profile data back. Inert
# unless PDL_API_KEY is set, so the $0/offline default is unchanged.
PDL_ENRICH = "https://api.peopledatalabs.com/v5/person/enrich"

PERSONAL = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
            "aol.com", "proton.me", "protonmail.com", "gmx.com", "live.com"}

# What an email alone CANNOT get for free — and where it would actually come from.
NOT_FREE = [
    ("Name", "Vector (de-anon) · Google sign-in · or a broker append"),
    ("Job title / seniority", "Vector · LinkedIn · Clay"),
    ("Company / org type / size", "Vector · Clay"),
    ("Age / birthdate", "broker append (not from Google or the email)"),
    ("Household income / net worth", "broker append (modeled)"),
    ("Interests / intent", "your HubSpot behavior · Clay · broker"),
]


def _gravatar(email: str, cache: LLMCache) -> dict:
    h = hashlib.sha256(email.encode()).hexdigest()
    key = LLMCache.hash_input("gravatar_v2", email)

    def fetch() -> dict:
        import httpx
        r = httpx.get(f"https://gravatar.com/{h}.json",
                      headers={"User-Agent": "ProvenanceDemo/1.0"}, timeout=8)
        if r.status_code != 200:
            return {"found": False}
        e = (r.json().get("entry") or [{}])[0]
        return {"found": True, "name": e.get("displayName", ""),
                "location": e.get("currentLocation", ""),
                "photo": bool(e.get("thumbnailUrl")),
                "accounts": [a.get("shortname") for a in (e.get("accounts") or [])][:6]}

    try:
        return cache.get_or_compute(key, fetch)
    except Exception:
        return {"found": False, "error": True}


def _pdl_lookup(cache: LLMCache, **ident: str) -> dict:
    """One PDL call for a single identifier set (email= or profile=). min_likelihood=4 filters
    weak same-name matches (the wrong-person risk) while letting a confident LinkedIn match (≈9)
    through. Returns {} with no key / no match — never fabricates. Cached per identifier."""
    key = os.environ.get("PDL_API_KEY", "").strip()
    ident = {k: v for k, v in ident.items() if v}
    if not key or not ident:
        return {}
    ck = LLMCache.hash_input("pdl_v2", "|".join(f"{k}={v}" for k, v in sorted(ident.items())))

    def fetch() -> dict:
        import httpx
        r = httpx.get(PDL_ENRICH, params={**ident, "min_likelihood": 4},
                      headers={"X-Api-Key": key}, timeout=12)
        if r.status_code != 200:
            return {"_status": r.status_code}
        d = (r.json() or {}).get("data") or {}

        def s(v):  # free tier redacts some PII to a bool flag — keep only real strings
            return v.strip() if isinstance(v, str) and v.strip() else None

        def name_of(obj):  # PDL nests names under {"name": ...}
            return s((obj or {}).get("name")) if isinstance(obj, dict) else None
        past = []
        for e in (d.get("experience") or [])[1:4]:        # skip [0] = current role
            t, co = name_of(e.get("title")), name_of(e.get("company"))
            if t and co:
                past.append(f"{t} — {co}")
        edu = [name_of(e.get("school")) for e in (d.get("education") or [])]
        return {"name": s(d.get("full_name")), "title": s(d.get("job_title")),
                "company": s(d.get("job_company_name")), "location": s(d.get("location_name")),
                "linkedin": s(d.get("linkedin_url")), "industry": s(d.get("job_company_industry")),
                "company_size": s(d.get("job_company_size")),
                "skills": [x for x in (d.get("skills") or []) if isinstance(x, str)][:6],
                "past_roles": past[:3],
                "education": [x for x in edu if x][:3],
                "interests": [x for x in (d.get("interests") or []) if isinstance(x, str)][:4]}

    try:
        return cache.get_or_compute(ck, fetch)
    except Exception:
        return {}


def _pdl(email: str, linkedin: str, cache: LLMCache) -> dict:
    """Real person enrichment: try the email first; if it has no match, fall back to a known
    LinkedIn URL (the realistic 'Vector de-anon gave us the LinkedIn' path)."""
    r = _pdl_lookup(cache, email=email) if email else {}
    if not (r.get("name") or r.get("title")) and linkedin:
        r = _pdl_lookup(cache, profile=linkedin)
    return r


def _company_news(company: str, cache: LLMCache) -> str:
    try:
        from pipeline.enrichment.connectors import LiveNewsConnector

        class _R:
            pass
        r = _R(); r.company = company
        facts = LiveNewsConnector(cache).fetch(r)
        return facts[0].value if facts else ""
    except Exception:
        return ""


def enrich(email: str, mode: str | None = None, linkedin: str = "") -> dict:
    # Honor the project's enrichment opt-in: live (network) only when PROVENANCE_ENRICH=live,
    # else "off" (still returns the real, no-network signals: domain + account type).
    # `linkedin` is an optional fallback identifier (e.g. from Vector de-anon) used when the
    # email has no PDL match — exactly the operator's case.
    if mode is None:
        mode = "live" if config.enrich_live() else "off"
    email = (email or "").strip().lower()
    dom = email.split("@")[1] if "@" in email else ""
    personal = dom in PERSONAL
    real: list[dict] = [
        {"label": "Email domain", "value": dom or "(none)", "source": "parse", "real": True},
        {"label": "Account type", "value": "personal mailbox" if personal else "corporate domain",
         "source": "domain classify", "real": True},
    ]
    if mode == "live" and dom:
        cache = LLMCache()
        g = _gravatar(email, cache)
        if g.get("found") and (g.get("name") or g.get("photo")):
            val = " · ".join(x for x in [g.get("name"), g.get("location"),
                             (", ".join(g.get("accounts") or []))] if x) or "(profile exists)"
            real.append({"label": "Public profile (Gravatar)", "value": val,
                         "source": "Gravatar (free, by email hash)", "real": True})
        else:
            real.append({"label": "Public profile (Gravatar)",
                         "value": "none — this email has no public Gravatar",
                         "source": "Gravatar", "real": True})
        # REAL person enrichment (People Data Labs) — email first, LinkedIn fallback. Only adds
        # rows it actually returns.
        p = _pdl(email, linkedin, cache)
        for label, val in (("Name", p.get("name")), ("Job title", p.get("title")),
                           ("Company", p.get("company")), ("Industry", p.get("industry")),
                           ("Company size", p.get("company_size")), ("Location", p.get("location")),
                           ("LinkedIn", p.get("linkedin"))):
            if val:
                real.append({"label": label, "value": val,
                             "source": "People Data Labs (live)", "real": True})
        if not personal:
            co = dom.split(".")[0].replace("-", " ").title()
            news = _company_news(co, cache)
            real.append({"label": "Company news", "value": news or "(no recent public news found)",
                         "source": "public news RSS (live)", "real": True})
            real.append({"label": "Company firmographics", "value": f"available for {dom} via Vector / Clay (not loaded)",
                         "source": "Vector · Clay", "real": False})
    have = sum(1 for r in real if r["real"] and "none" not in r["value"] and "no recent" not in r["value"])
    return {"email": email, "domain": dom, "personal": personal,
            "real": real, "not_free": [{"label": l, "where": w} for l, w in NOT_FREE],
            "have_count": have, "mode": mode}
