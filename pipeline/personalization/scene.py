"""Live firmographic-personalization engine for /demo/live.

The interactive "as if loaded from that IP" demo: a real landing page whose copy + backdrop
are chosen by (region × industry).

What's REAL here (the honest line the product draws):
  • LOCATION is detected from the visitor's real IP (server-side geo lookup, ipwho.is). Real.
  • INDUSTRY is a selectable NAICS taxonomy — in production this resolves via reverse-IP
    firmographic (a paid IP-intelligence provider, not wired). So it's honestly a *selector*.
  • COPY is deterministic templates per (region × industry) — provable, instant, no LLM.
  • IMAGERY is a curated library of REAL, Creative-Commons-licensed photos (fetched from
    Openverse, baked here) — each carries its creator + license in the receipt. Not AI-generated.

Surface policy: geo + firmographic are `allude` (involuntary signals — shape, don't recite);
the image source is `say` (we disclose exactly which licensed asset + its license).
"""
from __future__ import annotations

import ipaddress
import os

import httpx

from pipeline.common.cache import LLMCache

# --- curated, license-tagged image library (real CC photos, verified loading) --------------
# Baked from Openverse (commercial-use CC) on 2026-06-24; each carries creator + license.
_IMG = {
    "mining": {"url": "https://live.staticflickr.com/8752/17015286671_80312700b5_b.jpg",
               "creator": "docentjoyce", "license": "CC BY 2.0",
               "license_url": "https://creativecommons.org/licenses/by/2.0/",
               "landing": "https://www.flickr.com/photos/99003655@N00/17015286671", "id": "mining-01"},
    "energy": {"url": "https://live.staticflickr.com/2824/11346518126_8ed691da71_b.jpg",
               "creator": "Dai Luo", "license": "CC BY 2.0",
               "license_url": "https://creativecommons.org/licenses/by/2.0/",
               "landing": "https://www.flickr.com/photos/57669526@N04/11346518126", "id": "energy-01"},
    "agriculture": {"url": "https://live.staticflickr.com/197/460142568_8c71ae818b_b.jpg",
               "creator": "futureatlas.com", "license": "CC BY 2.0",
               "license_url": "https://creativecommons.org/licenses/by/2.0/",
               "landing": "https://www.flickr.com/photos/87913776@N00/460142568", "id": "agri-01"},
    "logistics": {"url": "https://live.staticflickr.com/2643/3950741540_5856681dfa.jpg",
               "creator": "roger4336", "license": "CC BY-SA 2.0",
               "license_url": "https://creativecommons.org/licenses/by-sa/2.0/",
               "landing": "https://www.flickr.com/photos/24736216@N07/3950741540", "id": "logi-01"},
    "healthcare": {"url": "https://live.staticflickr.com/4125/5063239777_0daf0995d2_b.jpg",
               "creator": "D-Stanley", "license": "CC BY 2.0",
               "license_url": "https://creativecommons.org/licenses/by/2.0/",
               "landing": "https://www.flickr.com/photos/79721788@N00/5063239777", "id": "health-01"},
    "manufacturing": {"url": "https://upload.wikimedia.org/wikipedia/commons/2/29/001_Car_factory_assembly_line_-_Opel_factory_in_Gliwice%2C_Poland.jpg",
               "creator": "Marek Ślusarczyk (Tupungato)", "license": "CC BY 3.0",
               "license_url": "https://creativecommons.org/licenses/by/3.0/",
               "landing": "https://commons.wikimedia.org/w/index.php?curid=116381354", "id": "mfg-01"},
    "technology": {"url": "https://live.staticflickr.com/5512/11387262366_0e6dd08fb7_b.jpg",
               "creator": "Cory M. Grenier", "license": "CC BY-SA 2.0",
               "license_url": "https://creativecommons.org/licenses/by-sa/2.0/",
               "landing": "https://www.flickr.com/photos/26087974@N05/11387262366", "id": "tech-01"},
    "construction": {"url": "https://live.staticflickr.com/6088/6130971504_75ac6f3d27_b.jpg",
               "creator": "lucyrfisher", "license": "CC BY 2.0",
               "license_url": "https://creativecommons.org/licenses/by/2.0/",
               "landing": "https://www.flickr.com/photos/37553027@N02/6130971504", "id": "constr-01"},
}

# --- industries: NAICS sector + deterministic copy template ({region} filled at render) ----
INDUSTRIES = [
    {"key": "mining", "label": "Mining & metals", "naics": "212", "accent": "#B5731B",
     "eyebrow": "For {region} mining & hard-rock operators",
     "headline": "Engineered for the pace of the pit.",
     "sub": "Built for operators across {region} — from extraction to haul to plant.",
     "cta": "Talk to a mining-ops lead"},
    {"key": "energy", "label": "Energy & utilities", "naics": "221", "accent": "#1E6FA8",
     "eyebrow": "For {region} energy operators",
     "headline": "Built for uptime, from wellhead to grid.",
     "sub": "The platform energy teams across {region} run their pipeline on.",
     "cta": "See it for energy"},
    {"key": "agriculture", "label": "Agriculture", "naics": "111", "accent": "#1E8A53",
     "eyebrow": "For {region} growers & ag operators",
     "headline": "Software that runs at the speed of the season.",
     "sub": "From planting to yield — built for growers across {region}.",
     "cta": "See it for ag"},
    {"key": "logistics", "label": "Logistics & freight", "naics": "488", "accent": "#5B5BD6",
     "eyebrow": "For {region} logistics & freight",
     "headline": "Move every container without moving the goalposts.",
     "sub": "Built for freight and 3PL teams across {region}.",
     "cta": "See it for logistics"},
    {"key": "healthcare", "label": "Healthcare", "naics": "622", "accent": "#0E9BAB",
     "eyebrow": "For {region} health systems",
     "headline": "Built for care teams, not paperwork.",
     "sub": "The platform health systems across {region} standardize on.",
     "cta": "Talk to a health-systems lead"},
    {"key": "manufacturing", "label": "Manufacturing", "naics": "31-33", "accent": "#6B4BD6",
     "eyebrow": "For {region} manufacturers",
     "headline": "Built for the floor, not the spreadsheet.",
     "sub": "From line to ledger — built for manufacturers across {region}.",
     "cta": "See it for manufacturing"},
    {"key": "technology", "label": "Technology", "naics": "5415", "accent": "#2E6FF5",
     "eyebrow": "For {region} technology teams",
     "headline": "The revenue platform engineered for scale.",
     "sub": "Built for software and tech teams across {region}.",
     "cta": "Start for free"},
    {"key": "construction", "label": "Construction", "naics": "236", "accent": "#C2761A",
     "eyebrow": "For {region} builders & contractors",
     "headline": "Built to keep every job on schedule.",
     "sub": "From bid to closeout — built for contractors across {region}.",
     "cta": "See it for construction"},
]
BY_KEY = {i["key"]: i for i in INDUSTRIES}

# US states for the location picker (the override list)
STATES = ["Arizona", "California", "Texas", "New York", "Florida", "Illinois", "Washington",
          "Colorado", "Georgia", "Pennsylvania", "Ohio", "North Carolina", "Nevada", "Oregon",
          "Michigan", "Massachusetts", "Minnesota", "Louisiana", "Oklahoma", "Wyoming"]

DEFAULT_INDUSTRY = "mining"
GENERIC_REGION = "your region"

# REAL reverse-IP provider (free, no key): geo + the org/company behind the IP + mobile/proxy/
# hosting flags so we know whether it's a clean corporate office IP vs an ISP/VPN/cloud.
_IP_API = "http://ip-api.com/json/"
_IP_FIELDS = "status,country,countryCode,region,regionName,city,isp,org,as,asname,mobile,proxy,hosting,query"
# REAL company → industry: PDL company-enrich (inert without PDL_API_KEY).
_PDL_COMPANY = "https://api.peopledatalabs.com/v5/company/enrich"

# map a free-text industry (from PDL) → our nearest sector bucket
_IND_HINTS = {
    "mining": ["mining", "metal", "mineral", "coal"],
    "energy": ["energy", "oil", "gas", "utilit", "power", "petroleum", "renewable"],
    "agriculture": ["farm", "agricultur", "ranch", "crop", "dairy"],
    "logistics": ["logistic", "freight", "shipping", "transport", "supply chain", "trucking", "warehous"],
    "healthcare": ["health", "hospital", "medical", "pharma", "biotech"],
    "manufacturing": ["manufactur", "industrial", "machinery", "automotive", "factory"],
    "technology": ["software", "information technology", "internet", "computer", "saas", "tech", "data"],
    "construction": ["construct", "building", "contractor", "civil engineering"],
}


def _industry_to_bucket(industry: str | None) -> str | None:
    if not industry:
        return None
    s = industry.lower()
    for key, hints in _IND_HINTS.items():
        if any(h in s for h in hints):
            return key
    return None


def client_ip(request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


def reverse_ip(ip: str) -> dict:
    """REAL reverse-IP (ip-api.com): geo + the company/org behind the IP + network flags.
    Cached per IP, short timeout, never raises. {} for private/loopback or any failure."""
    if not ip:
        return {}
    try:
        a = ipaddress.ip_address(ip)
        if a.is_private or a.is_loopback:
            return {}
    except ValueError:
        return {}
    cache = LLMCache()
    ck = LLMCache.hash_input("ipapi_v1", ip)

    def fetch() -> dict:
        r = httpx.get(_IP_API + ip, params={"fields": _IP_FIELDS}, timeout=4.0)
        d = r.json()
        return d if d.get("status") == "success" else {}

    try:
        d = cache.get_or_compute(ck, fetch)
    except Exception:
        d = {}
    if not d:
        return {}
    return {"region": d.get("regionName"), "city": d.get("city"), "country": d.get("country"),
            "company": (d.get("org") or d.get("asname") or "").strip(), "isp": d.get("isp"),
            "asname": d.get("asname"), "mobile": bool(d.get("mobile")),
            "proxy": bool(d.get("proxy")), "hosting": bool(d.get("hosting")),
            "is_corporate": not (d.get("mobile") or d.get("proxy") or d.get("hosting"))}


def _pdl_company_industry(name: str) -> str | None:
    """REAL company → industry via PDL company-enrich. Inert without PDL_API_KEY. Cached."""
    key = os.environ.get("PDL_API_KEY", "").strip()
    name = (name or "").strip()
    if not key or not name:
        return None
    cache = LLMCache()
    ck = LLMCache.hash_input("pdl_company_v1", name.lower())

    def fetch() -> dict:
        r = httpx.get(_PDL_COMPANY, params={"name": name, "min_likelihood": 2},
                      headers={"X-Api-Key": key}, timeout=8)
        if r.status_code != 200:
            return {}
        d = r.json() or {}
        d = d.get("data") or d
        return {"industry": d.get("industry")}

    try:
        return (cache.get_or_compute(ck, fetch) or {}).get("industry")
    except Exception:
        return None


def detect(request) -> dict:
    """Resolve the visitor from their REAL IP: region + company (reverse-IP) + industry (PDL).
    Honest about *why* it couldn't resolve a company (mobile / VPN / cloud / residential)."""
    ip = client_ip(request)
    rv = reverse_ip(ip)
    company = rv.get("company") if rv.get("is_corporate") else None
    industry, industry_raw = None, None
    if company:
        industry_raw = _pdl_company_industry(company)
        industry = _industry_to_bucket(industry_raw)
    reason = ""
    if not rv:
        reason = "local/unreachable IP — pick a location to preview"
    elif rv.get("mobile"):
        reason = f"mobile network ({rv.get('isp')}) — no company resolved"
    elif rv.get("proxy"):
        reason = "VPN/proxy detected — no company resolved"
    elif rv.get("hosting"):
        reason = f"hosting/cloud IP ({rv.get('isp')}) — not a corporate office"
    elif not company:
        reason = f"residential ISP ({rv.get('isp')}) — no company resolved"
    return {"ip": ip, "region": rv.get("region"), "city": rv.get("city"), "company": company,
            "industry": industry, "industry_raw": industry_raw, "isp": rv.get("isp"),
            "resolved_company": bool(company), "resolved_industry": bool(industry), "reason": reason}


def _fill(s: str, region: str | None) -> str:
    return s.replace("{region}", region or GENERIC_REGION)


def build_scene(region: str | None, industry_key: str, *, detected: bool = False,
                company: str | None = None) -> dict:
    """Deterministic (region × industry) → copy + image + provenance receipt. No network."""
    ind = BY_KEY.get(industry_key, BY_KEY[DEFAULT_INDUSTRY])
    img = _IMG.get(ind["key"], _IMG[DEFAULT_INDUSTRY])
    loc_note = "detected from your IP" if detected else "preview — you set this"
    receipt = []
    if company:
        receipt.append({"signal": f"company: {company}", "source": "Reverse-IP (ip-api.com)",
                        "policy": "allude", "role": "resolved from your IP — involuntary, so allude"})
    receipt += [
        {"signal": f"location: {region or 'unknown'}", "source": "Geo-IP (ip-api.com)",
         "policy": "allude", "role": loc_note},
        {"signal": f"industry: {ind['label']} (NAICS {ind['naics']})",
         "source": ("Company → PDL firmographic" if company else "Reverse-IP firmographic"),
         "policy": "allude", "role": ("resolved via PDL" if company else "selected · production resolves from the IP")},
        {"signal": f"backdrop: {img['id']}", "source": f"Curated library · {img['license']}",
         "policy": "say", "role": f"by {img['creator']} — disclosed, licensed"},
        {"signal": f"copy template: {ind['key']}", "source": "Deterministic rule",
         "policy": "say", "role": "templated, not generated"},
    ]
    return {
        "industry": ind["key"], "industry_label": ind["label"], "naics": ind["naics"],
        "accent": ind["accent"], "region": region or GENERIC_REGION,
        "eyebrow": _fill(ind["eyebrow"], region),
        "headline": _fill(ind["headline"], region),
        "sub": _fill(ind["sub"], region),
        "cta": ind["cta"], "image": img, "receipt": receipt,
    }


def client_map() -> list[dict]:
    """The industry → {copy templates, image} map embedded for instant client-side re-render."""
    return [{"key": i["key"], "label": i["label"], "naics": i["naics"], "accent": i["accent"],
             "eyebrow": i["eyebrow"], "headline": i["headline"], "sub": i["sub"], "cta": i["cta"],
             "image": _IMG.get(i["key"], _IMG[DEFAULT_INDUSTRY])} for i in INDUSTRIES]
