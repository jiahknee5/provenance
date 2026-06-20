"""Build a personalized landing page (UI + content) and a matching email for one person.

UI comes from the archetype (theme, hero kind, section order, CTA). Content is filled from
the person's facts, and the **context tier (1–4)** gates how personal the copy goes — reusing
the surface policy: tier 1 = declared/professional only (say), tier 2 adds first-party
behavior (allude/steer), tier 3 adds inferred segments (source hidden), tier 4 switches the
policy off and prints the deep synthetic facts verbatim, each provenance-tagged.
"""
from __future__ import annotations

from pipeline.personalization import design as DESIGN
from pipeline.personalization import segments as SEG

SECTION_CONTENT = {
    "outcomes": ("Graduate outcomes", "Median +$38K within six months; 600+ hired."),
    "curriculum": ("What you'll build", "12 weeks · 6 shipped projects · live instructors."),
    "financing": ("Financing & scholarships", "Pay monthly, defer until hired, or apply for a need-based scholarship."),
    "start-dates": ("Next cohorts", "Night cohort starts in 3 weeks; weekend intensive in 5."),
    "what-you-learn": ("What you'll learn", "Python → shipping an AI product. No prior ML needed."),
    "stories": ("Student stories", "Baristas, analysts, PMs — real switchers, real jobs."),
    "next-step": ("Your next step", "You finished Intro to Python — the night cohort picks up there."),
    "whats-new": ("New since you were here", "A new agents module and an alumni hiring network."),
    "credibility": ("Why teams trust us", "Instructors from top labs; used by 40+ companies."),
    "instructors": ("Your instructors", "Practitioners who ship AI in production."),
}


# The archetype's "offer" — composes as "{first}, {angle}." and escalates the same across tiers;
# only HOW personally we frame it changes per tier (below).
ANGLE = {
    "outcome":     ("here's where this takes your salary",  "See exactly where our graduates land."),
    "financing":   ("switch into AI without going broke",   "Scholarships, deferred tuition, and monthly plans."),
    "apply":       ("let's make it official",               "Finish your application — the next cohort is filling up."),
    "intro":       ("start with a free class",              "No commitment — see how we teach before you decide."),
    "welcome":     ("pick up right where you left off",      "Your Intro to Python progress is saved."),
    "credibility": ("bring real AI capability to your team", "Trusted by 40+ engineering orgs to upskill their teams."),
}


def _role_word(p: dict) -> str:
    """A tasteful industry word for the tier-2 ALLUSION — never the specific company name."""
    return (p.get("linkedin", {}).get("industry") or "").strip().lower() or "your field"


def _hero(arch: dict, p: dict, tier: int) -> dict:
    """The hero copy is personalized PER TIER, on the surface policy:
       1 (say)     — first name + (if they told us) their declared goal. Nothing inferred.
       2 (allude)  — frame by their de-anonymized industry, never the company name.
       3 (inferred)— frame by the modeled segment we put them in.
       4 (reveal)  — name the de-anonymized title + company in the headline itself.
    """
    kind = arch["hero"]
    first = p["name"].split()[0]
    li = p["linkedin"]
    title, company = li.get("title", ""), li.get("company", "")
    submitted = p.get("submitted", False)
    goal = (p.get("declared") or {}).get("goal", "")
    angle, base_sub = ANGLE.get(kind, ANGLE["intro"])

    if tier <= 1:
        head = f"{first}, {angle}."
        sub = f"You told us you want to {goal} — here's the fastest path." if (submitted and goal) else base_sub
    elif tier == 2:
        head = f"For {_role_word(p)} folks like you, {first} — {angle}."
        sub = base_sub
    elif tier == 3:
        head = f"For {arch['for']} — {first}, {angle}."
        sub = f"Tuned to the path most like yours. {base_sub}"
    else:  # tier 4 — the de-anonymization reveal, in the headline itself
        seen = f"{title} at {company}" if (title and company) else (title or company or "your profile")
        head = f"{first}, we noticed {seen} — {angle}."
        sub = f"Built from your de-anonymized visit. {base_sub}"
    return {"headline": head, "sub": sub}


def _personal_lines(p: dict, tier: int, arch: dict) -> list[dict]:
    """Tier-gated personalized lines, source-accurate (Vector / HubSpot / Clay).
    Vector firmographics are de-anonymized → `allude` (shape, don't recite); HubSpot form
    fields are declared → `say`; the de-anon reveal lands at tier 4."""
    raw = p.get("_raw", {})
    v, hs, cl = raw.get("vector", {}), raw.get("hubspot", {}), raw.get("clay", {})
    submitted = hs.get("submitted", False)
    goal = hs.get("interest_reason", "")
    first = p["name"].split()[0]
    lines: list[dict] = []

    def add(text, surface, frm, layer):
        lines.append({"text": text, "surface": surface, "from": frm, "layer": layer})

    # tier 1 — say: who they are by login + what they typed on a form
    add(f"Hi {first},", "say", "gauntletai login", "declared")
    if submitted and goal:
        add(f"You told us you want to {goal}.", "say", "HubSpot form · interest reason", "declared")

    # tier 2 — allude: Vector firmographic SHAPES the page (we de-anon'd it, they didn't tell us)
    if tier >= 2:
        co = v.get("company", "—")
        shape = (f"We tailored this for a {v.get('org_type', '').lower()} team like {co}."
                 if co not in ("—", "", None) else "We've tailored this to your background.")
        add(shape, "allude", "Vector · company / org type (de-anonymized)", "firmographic")
        if submitted and hs.get("top_pages"):
            add(f"We put {hs['top_pages'][0].replace('-', ' ')} front and center for you.",
                "allude", f"HubSpot · {hs.get('visits')} visits, pages viewed", "behavioral")

    # tier 3 — inferred: Clay + behavior modeled a segment
    if tier >= 3:
        add(f"Tuned for {arch['for']}.", "inferred", "modeled segments (Clay + behavior)", "segment")

    # tier 4 — creepy: the policy comes off and we stack EVERY layer we hold, each one tagged
    if tier >= 4:
        # ── layer: de-anonymized firmographic (Vector) ──
        noform = "" if submitted else " — even though you never filled out a form"
        loc = f", {v.get('location')}" if v.get("location") else ""
        add(f"We de-anonymized your visit{noform}: {v.get('job_title')} at {v.get('company')}{loc}.",
            "creepy", "Vector de-anonymization", "firmographic")
        if cl.get("company_meta"):
            add(f"…and profiled the employer: {cl['company_meta']}.",
                "creepy", "firmographic enrichment", "firmographic")
        # ── layer: enrichment append (Clay/PDL) — career, education, skills, interests, income ──
        if cl.get("past_roles"):
            add(f"Your trajectory before this: {' ← '.join(cl['past_roles'])}.",
                "creepy", "Clay/PDL · employment history", "enrichment")
        if cl.get("education"):
            add(f"Your schools: {', '.join(cl['education'])}.",
                "creepy", "Clay/PDL · education", "enrichment")
        if cl.get("skills"):
            add(f"Your listed skills ({', '.join(cl['skills'][:4])}) tell us to skip the basics and lead with the agents module.",
                "creepy", "Clay/PDL · skills", "enrichment")
        if cl.get("interests"):
            add(f"Off the clock you're into {', '.join(cl['interests'][:3])} — useful for a rep's small talk.",
                "creepy", "Clay/PDL · interests", "enrichment")
        if cl.get("income_band", "—") not in ("—", "", None):
            add(f"A modeled income of {cl['income_band']} — so we'd quietly pre-pick a payment plan.",
                "creepy", "Clay enrichment waterfall", "enrichment")
        # ── layer: behavioral (HubSpot) — only if they actually engaged ──
        if submitted and hs.get("abandoned"):
            add(f"You bailed at the {hs['abandoned']} — we'd nudge you straight back to it.",
                "creepy", f"HubSpot · {hs.get('visits')} visits", "behavioral")
        if submitted and hs.get("lead_score"):
            add(f"Your lead score is {hs['lead_score']} — high enough that a human rep gets paged.",
                "creepy", "HubSpot · lead score", "behavioral")
        # ── layer: identity graph + context ──
        if cl.get("profiles"):
            add(f"We matched {len(cl['profiles'])} of your social profiles ({', '.join(cl['profiles'])}).",
                "creepy", "identity match", "social")
        add(f"You came by at {v.get('visit_time')}; we logged it.",
            "creepy", "Vector · visit timestamp", "context")
    return lines


def _email(p: dict, arch: dict, lines: list[dict]) -> dict:
    first = p["name"].split()[0]
    subject = {
        "outcomes_first": f"{first}, here's where this could take your salary",
        "cost_confident": f"{first}, the scholarship + financing options you asked about",
        "fast_track": f"{first}, your application's almost done",
        "explorer": f"{first}, want to see a class before you commit?",
        "welcome_back": f"Welcome back, {first} — your next step",
        "prestige": f"{first}, bringing AI to your team",
    }[arch["id"]]
    body = [l["text"] for l in lines if l["surface"] in ("say", "allude")][:3]
    return {"subject": subject, "preview": body[0] if body else "", "body": body, "cta": arch["cta"]}


def _personalize_sections(sections: list[dict], p: dict, tier: int) -> list[dict]:
    """Tier-gated personalization woven INTO the section bodies, not just the hero."""
    if tier < 3:
        return sections
    li = p["linkedin"]
    industry, company = (li.get("industry") or "").strip(), li.get("company", "")
    cl = (p.get("_raw") or {}).get("clay", {})
    out = []
    for s in sections:
        sid, extra = s["id"], ""
        if sid == "outcomes" and industry:
            extra = (f" People who came from {industry} like you see the biggest lift."
                     if tier >= 4 else f" Especially for people moving out of {industry}.")
        elif sid in ("curriculum", "what-you-learn") and tier >= 4 and cl.get("skills"):
            extra = f" You already have {', '.join(cl['skills'][:2])} — you'd start past the fundamentals."
        elif sid == "financing" and tier >= 4 and cl.get("income_band"):
            extra = " We'd pre-select the plan our model fits to you."
        elif sid == "credibility" and tier >= 4 and company:
            extra = f" The rigor a {company}-scale org expects."
        out.append({**s, "body": s["body"] + extra})
    return out


def _cta(arch: dict, p: dict, tier: int) -> str:
    base = arch["cta"]
    if tier >= 4:                       # address them by name at the most personal tier
        return f"{p['name'].split()[0]} — {base[0].lower()}{base[1:]}"
    return base


def build_landing(p: dict, tier: int = 2) -> dict:
    tier = max(1, min(4, int(tier)))
    segs = SEG.derive(p)
    arch = SEG.pick_archetype(p, segs)
    design = DESIGN.design_for(p, segs, arch)
    lines = _personal_lines(p, tier, arch)
    sections = _personalize_sections(
        [{"id": s, "title": SECTION_CONTENT[s][0], "body": SECTION_CONTENT[s][1]}
         for s in arch["sections"] if s in SECTION_CONTENT], p, tier)
    layers = sorted({l["layer"] for l in lines})
    return {
        "id": p["id"], "name": p["name"], "email": p["email"],
        "tier": tier, "tier_meta": SEG.TIERS[tier],
        "archetype": arch, "segments": segs, "design": design,
        "hero": _hero(arch, p, tier),
        "personal_lines": lines,
        "layers": layers,
        "sections": sections,
        "cta": _cta(arch, p, tier),
        "email_preview": _email(p, arch, lines),
        "explanation": SEG.explain(p, tier),
    }
