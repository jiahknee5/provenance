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
_IP_FIELDS = ("status,country,countryCode,region,regionName,city,zip,lat,lon,timezone,"
              "isp,org,as,asname,mobile,proxy,hosting,query")
# REAL company → industry: PDL company-enrich (inert without PDL_API_KEY).
_PDL_COMPANY = "https://api.peopledatalabs.com/v5/company/enrich"

# map a free-text industry (from PDL's taxonomy) → our nearest sector bucket
_IND_HINTS = {
    "mining": ["mining", "metal", "mineral", "coal"],
    "energy": ["energy", "oil", "gas", "utilit", "power", "petroleum", "renewable", "solar", "nuclear"],
    "agriculture": ["farm", "agricultur", "ranch", "crop", "dairy", "fishery"],
    "logistics": ["logistic", "freight", "shipping", "transport", "supply chain", "trucking",
                  "warehous", "maritime", "aviation", "airline", "railroad"],
    "healthcare": ["health", "hospital", "medical", "pharma", "biotech", "wellness"],
    "manufacturing": ["manufactur", "industrial", "machinery", "automotive", "factory",
                      "electrical", "chemical", "plastics", "consumer goods", "textiles", "packaging"],
    "technology": ["software", "information technology", "internet", "computer", "saas", "tech",
                   "data", "electronics", "semiconductor", "telecommunic", "fintech", "information services"],
    "construction": ["construct", "building", "contractor", "civil engineering", "architecture"],
}


# consumer ISPs / carriers — the org behind a residential or mobile IP is the *provider*,
# not a company. ip-api's flags miss most of these, so we classify by name (high-precision).
_ISP_HINTS = ("at&t", "att services", "comcast", "xfinity", "verizon", "spectrum", "charter",
              "cox communications", "centurylink", "lumen", "t-mobile", "sprint", "frontier",
              "windstream", "mediacom", "optimum", "altice", "suddenlink", "starlink", "viasat",
              "hughesnet", "google fiber", "earthlink", "metronet", "wow!", "rcn", "ziply",
              "telus", "rogers", "bell canada", "shaw", "vodafone", "deutsche telekom", "telefonica",
              "broadband", "cable internet", "fios", "u-verse", "wireless", "cellular", "dsl")


def _looks_like_isp(*names: str) -> bool:
    s = " ".join(n.lower() for n in names if n)
    return any(h in s for h in _ISP_HINTS)


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
    is_isp = _looks_like_isp(d.get("org"), d.get("isp"), d.get("asname"))
    return {"region": d.get("regionName"), "city": d.get("city"), "country": d.get("country"),
            "zip": d.get("zip"), "lat": d.get("lat"), "lon": d.get("lon"),
            "timezone": d.get("timezone"), "asn": d.get("as"),
            "company": (d.get("org") or d.get("asname") or "").strip(), "isp": d.get("isp"),
            "org": d.get("org"), "asname": d.get("asname"), "mobile": bool(d.get("mobile")),
            "proxy": bool(d.get("proxy")), "hosting": bool(d.get("hosting")), "is_isp": is_isp,
            "is_corporate": not (d.get("mobile") or d.get("proxy") or d.get("hosting") or is_isp)}


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


def _daypart(tz: str | None) -> str | None:
    if not tz:
        return None
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        h = datetime.now(ZoneInfo(tz)).hour
    except Exception:
        return None
    return ("late night" if h >= 22 or h < 5 else "morning" if h < 12
            else "afternoon" if h < 17 else "evening")


def resolve_ip(ip: str) -> dict:
    """Resolve ANY IP → EVERY signal captured + the derivation cascade. Used for the visitor's
    own IP (default) and an entered IP (override). Returns a `captured` list (signal → value →
    what it drives → surface policy) so the page can show the whole pipeline transparently."""
    ip = (ip or "").strip()
    rv = reverse_ip(ip)
    company = rv.get("company") if rv.get("is_corporate") else None
    industry_raw = _pdl_company_industry(company) if company else None
    industry = _industry_to_bucket(industry_raw)
    daypart = _daypart(rv.get("timezone"))
    nettype = ("corporate" if rv.get("is_corporate") else "mobile" if rv.get("mobile")
               else "VPN / proxy" if rv.get("proxy") else "hosting / cloud" if rv.get("hosting")
               else "consumer ISP" if rv.get("is_isp") else "residential")
    reason = ""
    if not rv:
        reason = "local / private / unreachable IP — pick a location or try a public IP"
    elif rv.get("mobile"):
        reason = f"mobile network ({rv.get('isp')}) — no company resolved"
    elif rv.get("proxy"):
        reason = "VPN / proxy detected — no company resolved"
    elif rv.get("hosting"):
        reason = f"hosting / cloud IP ({rv.get('isp')}) — not a corporate office"
    elif rv.get("is_isp"):
        reason = f"consumer ISP ({rv.get('isp') or rv.get('org')}) — that's the provider, not a company. Reverse-IP only IDs a business on a corporate office IP; try a company's IP or a de-anon vendor."
    elif not company:
        reason = f"residential ISP ({rv.get('isp')}) — no company resolved"

    cap: list[dict] = []

    def add(label, value, drives, policy, group):
        cap.append({"label": label, "value": value if value not in (None, "") else "—",
                    "drives": drives, "policy": policy, "group": group})

    if rv:
        coords = (f"{rv.get('lat')}, {rv.get('lon')}" if rv.get("lat") is not None else None)
        ind_label = (BY_KEY[industry]["label"] + f" (NAICS {BY_KEY[industry]['naics']})") if industry else (industry_raw or None)
        add("Country", rv.get("country"), "—", "allude", "geo")
        add("Region / state", rv.get("region"), "region copy + image region", "allude", "geo")
        add("City", rv.get("city"), "headline (Say mode)", "allude", "geo")
        add("Postal", rv.get("zip"), "—", "allude", "geo")
        add("Coordinates", coords, "—", "allude", "geo")
        add("Timezone", rv.get("timezone"), "→ daypart", "allude", "geo")
        add("ASN", rv.get("asn"), "→ org / company", "allude", "net")
        add("ISP / org", rv.get("org") or rv.get("isp"), "→ company", "allude", "net")
        add("Network type", nettype, "gates company resolution", "observed", "net")
        add("Company", company, "→ industry", "allude", "resolved")
        add("Industry", ind_label, "copy template + backdrop", "allude", "resolved")
        add("Daypart", daypart, "tone / dark-mode (available)", "observed", "resolved")
    return {"ip": ip, "region": rv.get("region"), "city": rv.get("city"), "company": company,
            "industry": industry, "industry_raw": industry_raw, "isp": rv.get("isp"),
            "resolved_company": bool(company), "resolved_industry": bool(industry),
            "reason": reason, "captured": cap}


def detect(request) -> dict:
    """The visitor's own IP → resolution + the request-derived signals (device / language /
    referrer) that are captured but don't change when you override the IP."""
    d = resolve_ip(client_ip(request))
    ua = request.headers.get("user-agent", "")
    lang = (request.headers.get("accept-language", "") or "").split(",")[0]
    ref = request.headers.get("referer", "")
    device = "mobile" if ("Mobi" in ua or "Android" in ua) else "desktop"
    d["request_signals"] = [
        {"label": "Device (User-Agent)", "value": device, "drives": "layout (available)",
         "policy": "observed", "group": "request"},
        {"label": "Language", "value": lang or "—", "drives": "locale (available)",
         "policy": "observed", "group": "request"},
        {"label": "Referrer", "value": ref or "direct", "drives": "source attribution (available)",
         "policy": "observed", "group": "request"},
    ]
    return d


def _fill(s: str, region: str | None) -> str:
    return s.replace("{region}", region or GENERIC_REGION)


# SAY mode — the ungated version: recite the involuntary signals (company, precise location).
# Shown for contrast; in production the Gate blocks it (reciting allude-class data = overclaim).
SAY = {
    "eyebrow": "Resolved from your IP",
    "headline_co": "{company} — we see your {industry} team in {city}, {region}.",
    "headline_noco": "We see a {industry} operator in {region}.",
    "sub": "Down to the building. Most of your competitors already run us — want the same edge?",
}


def _say_fill(t: str, company, city, region, ind_label) -> str:
    return (t.replace("{company}", company or "your company")
             .replace("{industry}", (ind_label or "").lower())
             .replace("{city}", city or "your city")
             .replace("{region}", region or GENERIC_REGION))


def build_scene(region: str | None, industry_key: str, *, detected: bool = False,
                company: str | None = None, city: str | None = None,
                policy: str = "allude") -> dict:
    """Deterministic (region × industry × policy) → copy + image + provenance receipt. No network.
    policy='allude' ships (industry/region framing); policy='say' recites the company + precise
    location — the ungated version the Gate blocks in production, shown for contrast."""
    ind = BY_KEY.get(industry_key, BY_KEY[DEFAULT_INDUSTRY])
    img = _IMG.get(ind["key"], _IMG[DEFAULT_INDUSTRY])
    say = policy == "say"
    loc_note = "detected from your IP" if detected else "you set this"
    if say:
        eyebrow = SAY["eyebrow"]
        headline = _say_fill(SAY["headline_co"] if company else SAY["headline_noco"],
                             company, city, region, ind["label"])
        sub = _say_fill(SAY["sub"], company, city, region, ind["label"])
    else:
        eyebrow = _fill(ind["eyebrow"], region)
        headline = _fill(ind["headline"], region)
        sub = _fill(ind["sub"], region)
    p = "say" if say else "allude"
    recite = "RECITED — the Gate blocks this in production"
    receipt = []
    if company:
        receipt.append({"signal": f"company: {company}", "source": "Reverse-IP (ip-api.com)",
                        "policy": p, "role": recite if say else "resolved from your IP — involuntary, so allude"})
    receipt += [
        {"signal": f"location: {(city + ', ' if city and say else '') + (region or 'unknown')}",
         "source": "Geo-IP (ip-api.com)", "policy": p,
         "role": (recite if say else loc_note)},
        {"signal": f"industry: {ind['label']} (NAICS {ind['naics']})",
         "source": ("Company → PDL firmographic" if company else "Reverse-IP firmographic"),
         "policy": p, "role": (recite if say else ("resolved via PDL" if company else "selected · production resolves from the IP"))},
        {"signal": f"backdrop: {img['id']}", "source": f"Curated library · {img['license']}",
         "policy": "say", "role": f"by {img['creator']} — disclosed, licensed"},
        {"signal": f"copy template: {ind['key']}/{p}", "source": "Deterministic rule",
         "policy": "say", "role": "templated, not generated"},
    ]
    return {
        "industry": ind["key"], "industry_label": ind["label"], "naics": ind["naics"],
        "accent": ind["accent"], "region": region or GENERIC_REGION, "policy": policy,
        "blocked": say, "eyebrow": eyebrow, "headline": headline, "sub": sub,
        "cta": ind["cta"], "image": img, "receipt": receipt,
    }


def client_map() -> list[dict]:
    """The industry → {copy templates, image} map embedded for instant client-side re-render."""
    return [{"key": i["key"], "label": i["label"], "naics": i["naics"], "accent": i["accent"],
             "eyebrow": i["eyebrow"], "headline": i["headline"], "sub": i["sub"], "cta": i["cta"],
             "image": _IMG.get(i["key"], _IMG[DEFAULT_INDUSTRY])} for i in INDUSTRIES]
