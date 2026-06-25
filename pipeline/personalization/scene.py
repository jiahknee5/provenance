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
import json
import os
import pathlib

import httpx

from pipeline.common.cache import LLMCache

# --- curated, license-tagged image library (real CC photos, verified loading) --------------
# Baked from Openverse (commercial-use CC) on 2026-06-24; each carries creator + license.
# 2 real Creative-Commons photos per industry (Openverse-sourced, verified loading) — loaded
# from scene_images.json so the picker + design agent have options. Each carries creator + license.
GALLERY = json.loads((pathlib.Path(__file__).with_name("scene_images.json")).read_text())
_IMG = {k: v[0] for k, v in GALLERY.items()}    # primary image per industry (back-compat)

# curated example accounts — real corporate IPs verified against the live resolver (ip-api + PDL)
EXAMPLE_ACCOUNTS = json.loads((pathlib.Path(__file__).with_name("example_accounts.json")).read_text())


def image_for(industry_key: str, idx: int = 0) -> dict:
    imgs = GALLERY.get(industry_key) or GALLERY.get(DEFAULT_INDUSTRY) or [next(iter(_IMG.values()))]
    return imgs[idx % len(imgs)]

# --- industries: NAICS sector + deterministic copy template ({region} filled at render) ----
# "general" is the TRUE neutral fallback (no industry resolved) — not a specific sector. Its
# backdrop is a brand wash (no inferred imagery) and its copy leads with the product thesis.
INDUSTRIES = [
    {"key": "general", "label": "General", "naics": "—", "accent": "#3B5BD6",
     "eyebrow": "Provable personalization for teams in {region}",
     "headline": "Outreach that can’t say what it can’t prove.",
     "sub": "The GTM workspace that carries the source, basis, and surface policy behind every move.",
     "cta": "See how it works"},
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

DEFAULT_INDUSTRY = "general"   # TRUE neutral fallback when no industry resolves (not a sector)
GENERIC_REGION = "your region"

# REAL reverse-IP provider (free, no key): geo + the org/company behind the IP + mobile/proxy/
# hosting flags so we know whether it's a clean corporate office IP vs an ISP/VPN/cloud.
_IP_API = "http://ip-api.com/json/"
_IP_FIELDS = ("status,country,countryCode,region,regionName,city,zip,lat,lon,timezone,"
              "isp,org,as,asname,mobile,proxy,hosting,query")
# REAL company → industry: PDL company-enrich (inert without PDL_API_KEY).
_PDL_COMPANY = "https://api.peopledatalabs.com/v5/company/enrich"
# REAL email → person (title / seniority / company): PDL person-enrich. The first-party lane —
# works for ANY company size (a startup's domain IDs the company; reverse-IP can't).
_PDL_PERSON = "https://api.peopledatalabs.com/v5/person/enrich"
# personal mailboxes: a work email IDs a company, these don't.
_CONSUMER_DOMAINS = {"gmail.com", "googlemail.com", "yahoo.com", "ymail.com", "outlook.com",
                     "hotmail.com", "live.com", "msn.com", "icloud.com", "me.com", "mac.com",
                     "aol.com", "proton.me", "protonmail.com", "gmx.com", "mail.com", "yandex.com",
                     "zoho.com", "fastmail.com", "hey.com", "pm.me"}

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


# commercial VPN / proxy / Tor providers — the org behind a *consumer* VPN exit. Distinguishes
# a real corporate netblock (employee on the company VPN) from a privacy-VPN exit node.
_VPN_HINTS = ("nordvpn", "expressvpn", "mullvad", "surfshark", "proton vpn", "protonvpn",
              "private internet access", "cyberghost", "ipvanish", "tunnelbear", "windscribe",
              "vyprvpn", "purevpn", "strongvpn", "hotspot shield", "torguard", "perfect privacy",
              "hide.me", "mysterium", "datacamp limited", "m247", "tor exit", "tor network", "vpn")


def _looks_like_vpn(*names: str) -> bool:
    s = " ".join(n.lower() for n in names if n)
    return any(h in s for h in _VPN_HINTS)


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
    looks_vpn = _looks_like_vpn(d.get("org"), d.get("isp"), d.get("asname"))
    mobile, proxy, hosting = bool(d.get("mobile")), bool(d.get("proxy")), bool(d.get("hosting"))
    org = (d.get("org") or d.get("asname") or "").strip()
    # corporate-VPN exception: the proxy flag is set, but the org looks like a real company
    # (not a commercial-VPN provider, not hosting, not a consumer ISP) → an employee egressing
    # via the company netblock. A genuine B2B signal — but capped at medium confidence downstream.
    corp_via_vpn = bool(proxy and org and not looks_vpn and not hosting and not is_isp and not mobile)
    is_corporate = bool(org) and not (mobile or hosting or is_isp) and (not proxy or corp_via_vpn)
    return {"region": d.get("regionName"), "city": d.get("city"), "country": d.get("country"),
            "zip": d.get("zip"), "lat": d.get("lat"), "lon": d.get("lon"),
            "timezone": d.get("timezone"), "asn": d.get("as"),
            "company": org, "isp": d.get("isp"),
            "org": d.get("org"), "asname": d.get("asname"), "mobile": mobile,
            "proxy": proxy, "hosting": hosting, "is_isp": is_isp, "looks_vpn": looks_vpn,
            "corp_via_vpn": corp_via_vpn, "is_corporate": is_corporate}


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


def _pdl_company_by_domain(domain: str) -> dict:
    """REAL domain → company name + industry via PDL company-enrich (website=). Inert/cached."""
    key = os.environ.get("PDL_API_KEY", "").strip()
    domain = (domain or "").strip().lower()
    if not key or not domain:
        return {}
    cache = LLMCache()
    ck = LLMCache.hash_input("pdl_company_web_v1", domain)

    def fetch() -> dict:
        r = httpx.get(_PDL_COMPANY, params={"website": domain, "min_likelihood": 2},
                      headers={"X-Api-Key": key}, timeout=8)
        if r.status_code != 200:
            return {}
        d = (r.json() or {}).get("data") or {}
        return {"name": d.get("display_name") or d.get("name"), "industry": d.get("industry")}

    try:
        return cache.get_or_compute(ck, fetch) or {}
    except Exception:
        return {}


def _pdl_person(email: str) -> dict:
    """REAL email → person (title / seniority / company / industry) via PDL person-enrich."""
    key = os.environ.get("PDL_API_KEY", "").strip()
    email = (email or "").strip().lower()
    if not key or not email:
        return {}
    cache = LLMCache()
    ck = LLMCache.hash_input("pdl_person_v1", email)

    def fetch() -> dict:
        r = httpx.get(_PDL_PERSON, params={"email": email, "min_likelihood": 4},
                      headers={"X-Api-Key": key}, timeout=8)
        if r.status_code != 200:
            return {}
        d = (r.json() or {}).get("data") or {}
        levels = d.get("job_title_levels") or []
        return {"name": d.get("full_name"), "title": d.get("job_title"),
                "seniority": (levels[0] if levels else None),
                "company": d.get("job_company_name"), "industry": d.get("job_company_industry")}

    try:
        return cache.get_or_compute(ck, fetch) or {}
    except Exception:
        return {}


def _company_from_domain(domain: str) -> str:
    """Honest fallback when PDL doesn't know a domain: the domain IS the identifier."""
    core = (domain or "").split(".")[0].replace("-", " ").strip()
    return core.title() if core else domain


def resolve_email(email: str) -> dict:
    """FIRST-PARTY identity key: a work email → company (domain) + person (PDL). Unlike the IP
    lane, these facts are `say` — the visitor told us directly, so we may recite them. Works for
    ANY company size: a startup's domain identifies the company even when reverse-IP only sees a CDN."""
    email = (email or "").strip()
    dom = email.split("@")[-1].lower() if "@" in email else ""
    bad = ("@" not in email) or ("." not in dom)
    cap: list[dict] = []

    def add(label, value, drives, policy, conf=None):
        cap.append({"label": label, "value": value if value not in (None, "") else "—",
                    "drives": drives, "policy": policy, "group": "email", "conf": conf})

    if bad:
        return {"email": email, "company": None, "industry": None, "tier": 0, "tier_label": TIER_LABELS[0],
                "region": None, "city": None, "resolved_company": False, "resolved_industry": False,
                "confidence": {"location": "none", "company": "none", "industry": "none"},
                "competitive_eligible": False, "captured": [], "person": {},
                "reason": "enter a work email (name@company.com)"}
    if dom in _CONSUMER_DOMAINS:
        add("Email", email, "first-party identity", "say", "high")
        add("Domain", dom, "→ company", "say", "high")
        return {"email": email, "company": None, "industry": None, "tier": 0, "tier_label": TIER_LABELS[0],
                "region": None, "city": None, "resolved_company": False, "resolved_industry": False,
                "confidence": {"location": "none", "company": "none", "industry": "none"},
                "competitive_eligible": False, "captured": cap, "person": {},
                "reason": f"{dom} is a personal mailbox — no company. A work email IDs the company."}

    person = _pdl_person(email)
    co = _pdl_company_by_domain(dom)
    company = person.get("company") or co.get("name") or _company_from_domain(dom)
    industry_raw = person.get("industry") or co.get("industry")
    industry = _industry_to_bucket(industry_raw)
    title, seniority, name = person.get("title"), person.get("seniority"), person.get("name")
    # first-party email → company is HIGH confidence (self-declared). Tier 2 once we have a sector.
    conf = {"location": "none", "company": "high",
            "industry": "high" if industry else ("low" if company else "none")}
    tier = 2 if (company and industry) else (1 if company else 0)
    ind_label = (BY_KEY[industry]["label"] + f" (NAICS {BY_KEY[industry]['naics']})") if industry else (industry_raw or None)

    add("Email", email, "first-party identity", "say", "high")
    add("Domain", dom, "→ company", "say", "high")
    add("Company", company, "→ industry", "say", "high")
    if name:
        add("Person", name, "personalization", "say", "high")
    if title:
        add("Title", title + (f" · {seniority}" if seniority else ""), "role-aware copy", "say", "high")
    add("Industry", ind_label, "copy template + backdrop", "say", conf["industry"])
    add("Personalization tier", f"{tier} · {TIER_LABELS[tier]}", "which copy path runs", "observed")

    reason = ("" if industry else
              (f"{company} resolved from {dom}, but no industry came back — neutral copy, no sector guessed"
               if company else f"couldn't resolve {dom}"))
    return {"email": email, "company": company, "industry": industry, "industry_raw": industry_raw,
            "region": None, "city": None, "tier": tier, "tier_label": TIER_LABELS[tier],
            "resolved_company": bool(company), "resolved_industry": bool(industry),
            "confidence": conf, "competitive_eligible": tier == 2, "captured": cap,
            "person": {"name": name, "title": title, "seniority": seniority}, "reason": reason}


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


# personalization tiers — the routing outcome (see /static/mockups/decision-tree.html).
# 0 neutral · 1 location-aware neutral · 2 firmographic · (3 = 2 + competitive, engaged by angle)
TIER_LABELS = {0: "neutral", 1: "location-aware", 2: "firmographic", 3: "firmographic + competitive"}


def _classify(rv: dict, company: str | None, industry: str | None) -> dict:
    """Deterministic router: real ip-api flags + whether PDL resolved an industry → network type,
    per-field confidence (location / company / industry), personalization tier, honest reason.
    No LLM, no network — pure and reproducible, so the routing is itself provable."""
    if not rv:
        return {"network_type": "private / unreachable", "tier": 0, "tier_label": TIER_LABELS[0],
                "confidence": {"location": "none", "company": "none", "industry": "none"},
                "competitive_eligible": False,
                "reason": "local / private / unreachable IP — pick a location or try a public IP"}
    mobile, proxy, hosting = rv.get("mobile"), rv.get("proxy"), rv.get("hosting")
    is_isp, corp_vpn, is_corp = rv.get("is_isp"), rv.get("corp_via_vpn"), rv.get("is_corporate")
    isp = rv.get("isp") or rv.get("org") or "the provider"

    if corp_vpn:   net = "corporate (via VPN)"
    elif is_corp:  net = "corporate"
    elif mobile:   net = "mobile"
    elif proxy:    net = "VPN / proxy"
    elif hosting:  net = "hosting / cloud"
    elif is_isp:   net = "consumer ISP"
    else:          net = "residential"

    # per-field confidence — each inference hop loses confidence
    loc = ("high" if net in ("corporate", "consumer ISP", "residential", "corporate (via VPN)")
           else "medium" if net == "mobile" else "low")   # VPN/proxy/hosting → datacenter geo
    comp = ("high" if (is_corp and not corp_vpn and company)
            else "medium" if (corp_vpn and company) else "none")
    ind_c = ("high" if (industry and comp == "high") else "medium" if (industry and comp == "medium")
             else "low" if (company and not industry) else "none")

    # tier: industry resolved → firmographic; geo-only → location-aware; nothing usable → neutral
    if company and industry:                                          tier = 2
    elif loc in ("high", "medium") and net not in ("hosting / cloud", "VPN / proxy"): tier = 1
    else:                                                             tier = 0
    competitive = tier == 2

    if net == "corporate (via VPN)":
        reason = (f"corporate VPN ({rv.get('org')}) — employee exiting via the company netblock; "
                  "a B2B signal, but capped at medium confidence")
    elif net == "corporate":
        reason = ("" if industry else
                  f"corporate IP ({rv.get('org')}) resolved, but PDL returned no industry — neutral copy, no sector guessed")
    elif mobile:
        reason = f"mobile network ({rv.get('isp')}) — no company; location is carrier-gateway coarse"
    elif proxy:
        reason = ("commercial VPN / proxy — the IP describes the exit node, not the visitor; "
                  "pivot to behavioral / first-party signals, don't fabricate firmographics")
    elif hosting:
        reason = f"hosting / cloud IP ({rv.get('isp')}) — not a human office (bot / scraper / VPN exit)"
    elif is_isp:
        reason = (f"consumer ISP ({isp}) — that's the provider, not a company. Reverse-IP only IDs a "
                  "business on a corporate office IP; try a company's IP or a de-anon vendor.")
    elif not company:
        reason = f"residential ISP ({rv.get('isp')}) — no company resolved"
    else:
        reason = ""
    return {"network_type": net, "tier": tier, "tier_label": TIER_LABELS[tier],
            "confidence": {"location": loc, "company": comp, "industry": ind_c},
            "competitive_eligible": competitive, "reason": reason}


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
    cls = _classify(rv, company, industry)        # deterministic router → type / confidence / tier
    nettype, reason, conf = cls["network_type"], cls["reason"], cls["confidence"]

    cap: list[dict] = []

    def add(label, value, drives, policy, group, conf=None):
        cap.append({"label": label, "value": value if value not in (None, "") else "—",
                    "drives": drives, "policy": policy, "group": group, "conf": conf})

    if rv:
        coords = (f"{rv.get('lat')}, {rv.get('lon')}" if rv.get("lat") is not None else None)
        ind_label = (BY_KEY[industry]["label"] + f" (NAICS {BY_KEY[industry]['naics']})") if industry else (industry_raw or None)
        add("Country", rv.get("country"), "—", "allude", "geo")
        add("Region / state", rv.get("region"), "region copy + image region", "allude", "geo", conf["location"])
        add("City", rv.get("city"), "headline (Say mode)", "allude", "geo")
        add("Postal", rv.get("zip"), "—", "allude", "geo")
        add("Coordinates", coords, "—", "allude", "geo")
        add("Timezone", rv.get("timezone"), "→ daypart", "allude", "geo")
        add("ASN", rv.get("asn"), "→ org / company", "allude", "net")
        add("ISP / org", rv.get("org") or rv.get("isp"), "→ company", "allude", "net")
        add("Network type", nettype, "gates company resolution", "observed", "net")
        add("Personalization tier", f"{cls['tier']} · {cls['tier_label']}", "which copy path runs", "observed", "net")
        add("Company", company, "→ industry", "allude", "resolved", conf["company"])
        add("Industry", ind_label, "copy template + backdrop", "allude", "resolved", conf["industry"])
        add("Daypart", daypart, "tone / dark-mode (available)", "observed", "resolved")
    return {"ip": ip, "region": rv.get("region"), "city": rv.get("city"), "company": company,
            "industry": industry, "industry_raw": industry_raw, "isp": rv.get("isp"),
            "daypart": daypart, "resolved_company": bool(company),
            "resolved_industry": bool(industry), "reason": reason, "captured": cap,
            "network_type": nettype, "tier": cls["tier"], "tier_label": cls["tier_label"],
            "confidence": conf, "competitive_eligible": cls["competitive_eligible"],
            "corp_via_vpn": bool(rv.get("corp_via_vpn"))}


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
