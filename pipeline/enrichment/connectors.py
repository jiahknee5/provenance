"""Enrichment connectors — each answers one question about the recipient and returns
RawFacts tagged with the source id the Enrichment Gate keys on.

Two are genuinely real and free (no new deps, no PII to third parties, $0):
  * EmailDomainConnector — pure parse of the domain the user gave us (no network).
  * LiveNewsConnector     — fetches a public news RSS keyed on the COMPANY name (urllib,
                            stdlib). Cached via LLMCache so a live run replays deterministically.
                            On no-network it returns nothing and the driver logs it honestly
                            — never a silent synthetic fallback.

The rest are simulated stand-ins for paid vendors (Clearbit/ZoomInfo/6sense class). In the
default `synthetic` mode the news connector is simulated too, so the demo is offline + $0 +
byte-identical. `config.enrich_live()` swaps in the real news connector.
"""
from __future__ import annotations

import hashlib
import html
import re
import urllib.parse
import urllib.request
from typing import Protocol

from pipeline.common import config
from pipeline.common.cache import LLMCache
from pipeline.enrichment.schemas import RawFact

_EHR = ["Epic", "Cerner/Oracle Health", "MEDITECH", "Allscripts/Veradigm"]
_NEWS_TEMPLATES = [
    "announced a value-based-care initiative",
    "opened a new regional facility",
    "was named to a regional Top Hospitals list",
    "expanded its telehealth program",
    "reported a push to cut administrative cost",
]
_INTENT_BY_ROLE = {
    "clinops": "reducing length of stay", "cfo": "lowering total cost of ownership",
    "it_security": "secure EHR integration", "quality": "outcome reporting",
}


def _h(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)


class Connector(Protocol):
    id: str
    label: str
    def fetch(self, recipient) -> list[RawFact]: ...


# --------------------------------------------------------------------------- #
# Real + free
# --------------------------------------------------------------------------- #
class EmailDomainConnector:
    id = "email_domain"
    label = "email domain parse (real, no network)"

    def fetch(self, recipient) -> list[RawFact]:
        dom = recipient.email.split("@")[-1].strip().lower() if "@" in recipient.email else ""
        if not dom:
            return []
        return [RawFact(key="company_domain", value=dom, source=self.id, confidence=0.99,
                        detail=f"parsed from {recipient.email.split('@')[0]}@…")]


class LiveNewsConnector:
    id = "company_news_rss"
    label = "public news RSS (LIVE, cached)"

    def __init__(self, cache: LLMCache | None = None):
        self.cache = cache or LLMCache()

    def _fetch_live(self, company: str) -> dict:
        url = ("https://news.google.com/rss/search?q="
               + urllib.parse.quote(f'"{company}"') + "&hl=en-US&gl=US&ceid=US:en")
        req = urllib.request.Request(url, headers={"User-Agent": "ProvenanceDemo/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml = resp.read().decode("utf-8", "ignore")
        titles = re.findall(r"<item>.*?<title>(.*?)</title>", xml, re.S)
        headline = html.unescape(re.sub(r"<.*?>", "", titles[0]).strip()) if titles else ""
        return {"headline": headline}

    def fetch(self, recipient) -> list[RawFact]:
        key = LLMCache.hash_input("news_rss", recipient.company)
        try:
            out = self.cache.get_or_compute(key, lambda: self._fetch_live(recipient.company))
        except Exception:
            return []   # honest: no network -> no fact (the driver logs unavailability)
        headline = (out or {}).get("headline", "")
        if not headline:
            return []
        return [RawFact(key="recent_news", value=headline, source=self.id, confidence=0.7,
                        detail="public news RSS (live, attributed)")]


# --------------------------------------------------------------------------- #
# Simulated (deterministic stand-ins for paid vendors) — offline, $0
# --------------------------------------------------------------------------- #
class SimNewsConnector:
    id = "company_news_rss"
    label = "public news (simulated, deterministic)"

    def fetch(self, recipient) -> list[RawFact]:
        item = _NEWS_TEMPLATES[_h(recipient.company) % len(_NEWS_TEMPLATES)]
        return [RawFact(key="recent_news", value=f"{recipient.company} {item}", source=self.id,
                        confidence=0.7, detail="synthetic public-news item")]


class SimFirmographicConnector:
    id = "firmographic_sim"
    label = "firmographics (simulated, Clearbit/ZoomInfo class)"

    def fetch(self, recipient) -> list[RawFact]:
        h = _h(recipient.company)
        facilities = h % 18 + 2
        ehr = _EHR[h % len(_EHR)]
        band = {"community": "1–2 hospitals", "regional": "3–8 hospitals",
                "idn": "9+ hospital IDN"}.get(recipient.company_size, "health system")
        return [
            RawFact(key="num_facilities", value=str(facilities), source=self.id, confidence=0.8,
                    detail="simulated firmographic"),
            RawFact(key="ehr_vendor", value=ehr, source=self.id, confidence=0.75,
                    detail="simulated firmographic"),
            RawFact(key="size_band", value=band, source=self.id, confidence=0.9,
                    detail="from declared company size"),
        ]


class SimIntentConnector:
    id = "intent_sim"
    label = "account intent (simulated, 6sense/Bombora class)"

    def fetch(self, recipient) -> list[RawFact]:
        topic = _INTENT_BY_ROLE.get(recipient.role, "clinical analytics")
        in_market = bool(_h("intent" + recipient.company) % 2)
        out = [RawFact(key="intent_topic", value=topic, source=self.id, confidence=0.6,
                       detail="simulated account-level surge signal")]
        if in_market:
            out.append(RawFact(key="in_market", value="true", source=self.id, confidence=0.55,
                               detail="simulated buying-stage signal"))
        return out


def connectors_for(mode: str | None = None) -> list:
    """The connector set for the mode. Email-domain parse is always real (no network).
    The news connector is live only in `live` mode; everything else is simulated."""
    mode = mode or config.ENRICH_MODE
    news = LiveNewsConnector() if mode == "live" else SimNewsConnector()
    return [EmailDomainConnector(), news, SimFirmographicConnector(), SimIntentConnector()]
