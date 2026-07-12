"""Design inference — turn a person's segments + signals into a full visual identity.

Beyond the archetype's accent, we infer the things that make two landing pages actually
*look* different: light/dark mode (from when they browse), a colour gradient, a type voice,
the hero composition, a motion level, a background motif, and the proof style. Each choice
records its evidence, so the admin "how this page was built" view explains the UI, not just
the copy. Everything is CSS-only and offline (no images, no web fonts, no CDN).
"""
from __future__ import annotations

# archetype → visual kit (gradient pair, hero composition, motion, motif, voice, proof)
KIT = {
    "outcomes_first": {"grad": ("#16b364", "#0aa3a3"), "hero": "stat", "motion": "subtle",
                       "motif": "rays", "voice": "confident", "proof": "stats",
                       "stat": ("+$38K", "median salary lift within 6 months")},
    "cost_confident": {"grad": ("#0e9bab", "#1f9d57"), "hero": "price", "motion": "subtle",
                       "motif": "mesh", "voice": "clear", "proof": "stats",
                       "stat": ("$0", "down — pay only once you're hired")},
    "fast_track": {"grad": ("#8a5cf6", "#d6409f"), "hero": "cta", "motion": "lively",
                   "motif": "orbs", "voice": "bold", "proof": "stats",
                   "stat": ("3 wks", "to your next cohort — seats filling")},
    "explorer": {"grad": ("#22b8cf", "#5b8def"), "hero": "soft", "motion": "lively",
                 "motif": "dots", "voice": "playful", "proof": "testimonial",
                 "stat": ("Free", "your first class — no commitment")},
    "welcome_back": {"grad": ("#f08c00", "#e8590c"), "hero": "continuity", "motion": "subtle",
                     "motif": "grid", "voice": "warm", "proof": "testimonial",
                     "stat": ("Level 2", "you're ready for the next step")},
    "prestige": {"grad": ("#5b6b7c", "#2b3a4d"), "hero": "credibility", "motion": "still",
                 "motif": "grid", "voice": "refined", "proof": "stats",
                 "stat": ("40+", "engineering orgs trust us")},
}

# light/dark palettes
DARK = {"bg": "#0b1018", "surface": "#141d2b", "ink": "#eef3f9", "mut": "#94a3b5", "line": "#23303f"}
LIGHT = {"bg": "#f6f8fc", "surface": "#ffffff", "ink": "#141d2b", "mut": "#5b6b7c", "line": "#e6ebf1"}

VOICE = {  # type treatment per voice
    "confident": {"weight": 800, "tracking": "-0.02em", "family": "system", "eyebrow_caps": False},
    "clear":     {"weight": 700, "tracking": "-0.01em", "family": "system", "eyebrow_caps": False},
    "bold":      {"weight": 900, "tracking": "-0.03em", "family": "system", "eyebrow_caps": True},
    "playful":   {"weight": 800, "tracking": "-0.01em", "family": "system", "eyebrow_caps": False},
    "warm":      {"weight": 800, "tracking": "-0.01em", "family": "system", "eyebrow_caps": False},
    "refined":   {"weight": 500, "tracking": "0.01em", "family": "serif", "eyebrow_caps": True},
}


def _has(segs, fam, sid):
    return any(s["id"] == sid for s in segs.get(fam, {}).get("segments", []))


def design_for(p: dict, segs: dict, arch: dict) -> dict:
    kit = KIT[arch["id"]]
    deep = p["deep"]
    ev: list[dict] = []

    # mode — when do they browse? night/evening → dramatic dark; daytime → clean light.
    daypart = deep.get("daypart", "day")
    night = any(w in daypart for w in ("night", "evening"))
    mode = "light" if arch["id"] in ("prestige", "welcome_back") else ("dark" if night else "light")
    pal = DARK if mode == "dark" else LIGHT
    ev.append({"dim": "mode", "value": mode,
               "why": f"observed local time = {daypart}" + (" (kept light for a refined/warm archetype)"
                      if arch["id"] in ("prestige", "welcome_back") else "")})

    # motion — lively for ambitious/explorers, still for prestige; honour reduced-motion in CSS.
    motion = kit["motion"]
    if _has(segs, "psychographic", "ambitious") and motion != "still":
        motion = "lively"
        ev.append({"dim": "motion", "value": "lively", "why": "psychographic: ambitious"})
    else:
        ev.append({"dim": "motion", "value": motion, "why": f"{arch['label']} archetype"})

    # proof style — data-driven (technical) get numbers; social-proof get a testimonial.
    proof = "stats" if _has(segs, "psychographic", "data_driven") else kit["proof"]
    ev.append({"dim": "proof", "value": proof,
               "why": "psychographic: " + ("data-driven → stats" if proof == "stats" else "social-proof → testimonial")})

    voice = kit["voice"]
    ev.append({"dim": "voice", "value": voice, "why": f"{arch['label']} archetype"})
    ev.append({"dim": "hero", "value": kit["hero"], "why": f"{arch['label']}: lead with the {kit['hero']}"})
    ev.append({"dim": "palette", "value": " → ".join(kit["grad"]), "why": "archetype gradient"})
    ev.append({"dim": "motif", "value": kit["motif"], "why": "archetype background"})

    vt = VOICE[voice]
    return {
        "mode": mode, "accent": kit["grad"][0], "accent2": kit["grad"][1],
        **pal, "voice": voice, "hero": kit["hero"], "motion": motion, "motif": kit["motif"],
        "proof": proof, "stat_big": kit["stat"][0], "stat_label": kit["stat"][1],
        "weight": vt["weight"], "tracking": vt["tracking"], "family": vt["family"],
        "eyebrow_caps": vt["eyebrow_caps"], "evidence": ev,
        "industry": p["linkedin"]["industry"], "seniority": p["linkedin"]["seniority"],
    }
