"""Showcase use-case demos — actual personalized landing pages built on the scene engine.

Each use case is a real, IP-personalized website (like /demo/live) for a named seller,
demonstrating one go-to-market shape. The seller's copy is personalized to the visitor's
detected industry + region; the licensed backdrop and the provenance receipt come straight
from the scene engine (`scene.build_scene`), so every personalized line carries its source.
Override the industry or region to preview what any visitor would get.

  1 · GauntletAI — anonymous visitor → a hero rewritten for their company / industry / region
  2 · SkyFi      — a geo-pinned operator → copy + backdrop tuned to their region and sector
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.personalization import scene as SC


@dataclass(frozen=True)
class UseCaseDemo:
    slug: str
    num: int
    brand: str
    domain: str
    category: str
    accent: str                 # the seller's brand accent (the CTA colour)
    default_industry: str       # what to show before anything is detected
    summary: str                # one line for the showcase index
    what_apt_does: str          # the story panel on the demo page
    angle: dict                 # GATED {eyebrow, headline, sub, cta} — {industry}/{region} only (ships)
    say_angle: dict             # UNGATED {eyebrow, headline, sub} — recites company/city (Gate blocks)


DEMOS: dict[str, UseCaseDemo] = {
    "gauntletai": UseCaseDemo(
        slug="gauntletai", num=1, brand="GauntletAI", domain="gauntletai.com",
        category="AI engineering training", accent="#7c5cff", default_industry="technology",
        summary="An anonymous visitor → a hero rewritten for their company, industry, and region.",
        what_apt_does=(
            "A first-time visitor lands with no identity. apt resolves their company, industry "
            "and region from the IP — before the page paints — and reframes GauntletAI's pitch to "
            "that exact team. Nothing the visitor didn't earn is recited; every personalized line "
            "carries a receipt. Flip the industry or region to preview what any visitor would see."),
        angle={
            "eyebrow": "For {industry} teams in {region}",
            "headline": "Your {industry} team is one cohort away from building with AI.",
            "sub": "Gauntlet trains {industry} engineers to ship with AI in 10 weeks — not 10 hires. "
                   "Built around how {region} teams actually work.",
            "cta": "See the {industry} track",
        },
        say_angle={
            "eyebrow": "Resolved from your IP",
            "headline": "{company} in {city} — one cohort from building with AI.",
            "sub": "We pulled your company and your office from your IP. Most {industry} teams near "
                   "{city} already train with us.",
        }),
    "skyfi": UseCaseDemo(
        slug="skyfi", num=2, brand="SkyFi", domain="skyfi.com",
        category="on-demand satellite imagery", accent="#1E6FA8", default_industry="mining",
        summary="A geo-pinned operator → copy and a backdrop tuned to their region and sector.",
        what_apt_does=(
            "A geography-dependent operator lands on the site. apt detects the business and its "
            "region + sector and tailors the copy — and the backdrop — to that operation. It frames "
            "the region, but won't pinpoint the exact site unless the visitor declares it (the "
            "creepiness ceiling). Change the region or sector to preview any operator's view."),
        angle={
            "eyebrow": "For {industry} operations across {region}",
            "headline": "See change across your {region} sites — on a weekly cadence.",
            "sub": "SkyFi delivers on-demand satellite imagery tuned to {industry} operators. "
                   "Point us at your area of interest; we image it.",
            "cta": "Image your {region} operations",
        },
        say_angle={
            "eyebrow": "Resolved from your IP",
            "headline": "{company} — we see your {industry} sites near {city}, {region}.",
            "sub": "Down to the parcel. We imaged your exact area of interest already — want the same "
                   "cadence on your operations?",
        }),
}
ORDER = ["gauntletai", "skyfi"]


def _fill(t: str, industry_label: str | None, region: str | None) -> str:
    ind = (industry_label or "your").lower()
    return t.replace("{industry}", ind).replace("{region}", region or SC.GENERIC_REGION)


def _fill_say(t: str, *, company, city, industry_label, region) -> str:
    return (t.replace("{company}", company or "your company")
             .replace("{city}", city or "your city")
             .replace("{industry}", (industry_label or "your").lower())
             .replace("{region}", region or SC.GENERIC_REGION))


def build(slug: str, *, region: str | None, industry: str | None,
          company: str | None = None, city: str | None = None, detected: bool = False) -> dict:
    """A personalized scene for this use case: real image + provenance receipt from the scene
    engine, with the seller's copy overridden + personalized to the (industry × region). Returns
    BOTH the gated version (ships) and the ungated version (recites company/city — the Gate blocks)."""
    d = DEMOS[slug]
    ind_key = industry or d.default_industry
    gated = SC.build_scene(region, ind_key, detected=detected, company=company, city=city, policy="allude")
    ungated = SC.build_scene(region, ind_key, detected=detected, company=company, city=city, policy="say")
    ind_label = gated["industry_label"]
    hero = {k: _fill(v, ind_label, region) for k, v in d.angle.items()}
    hero_say = {k: _fill_say(v, company=company, city=city, industry_label=ind_label, region=region)
                for k, v in d.say_angle.items()}
    return {"demo": d, "scene": gated, "scene_say": ungated, "hero": hero, "hero_say": hero_say}
