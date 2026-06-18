"""Per-segment A/B variants (the bandit arms) + the planted lie, and the function that
Gates the variant set into the action pool.

Personalization is slot-fill ({name}, {company}); the factual content is approved claim
text inlined verbatim by claim_id, so honest claims are verbatim-traceable and pass NLI
trivially. Only the planted-lie variant carries an unverifiable, guaranteed-outcome claim
— the Gate blocks it, so it never enters the constrained action pool.
"""
from __future__ import annotations

from typing import Optional

from pipeline.common.schemas import Variant
from pipeline.generation.recipients import ALL_SEGMENTS
from pipeline.library import seed_data

# role -> [(arm, angle, headline, claim_ids)]
ROLE_ANGLES: dict[str, list[tuple]] = {
    "clinops": [
        ("A", "outcomes", "Cut length of stay with verified analytics", ["c_los", "c_speed", "c_deployed"]),
        ("B", "speed", "Process a full claims dataset in under four hours", ["c_speed", "c_los", "c_deployed"]),
    ],
    "cfo": [
        ("A", "roi", "A verified cut in total cost of ownership", ["c_tco", "c_deployed", "c_price"]),
        ("B", "pricing", "Transparent pricing, no implementation fee", ["c_price", "c_nofee", "c_deployed"]),
    ],
    "it_security": [
        ("A", "security", "SOC 2 Type II, HIPAA, encrypted end to end", ["c_soc2", "c_hipaa", "c_encrypt"]),
        ("B", "integration", "Integrates with 30 EHR systems out of the box", ["c_ehr", "c_speed", "c_soc2"]),
    ],
    "quality": [
        ("A", "outcomes", "Improve outcomes with verified reporting", ["c_los", "c_deployed", "c_hipaa"]),
        ("B", "proof", "Deployed across 12 systems, HIPAA compliant", ["c_deployed", "c_hipaa", "c_los"]),
    ],
}
# the planted lie: one honest hook + an unverifiable guaranteed-outcome claim
LIE_ANGLE = ("LIE", "lie", "Guaranteed 60% fewer readmissions — risk-free", ["c_deployed"])

CHANNEL_TEMPLATES = {
    "email": ("Hi {name},\n\n{headline}.\n{claims}\n\n"
              "Worth a 20-minute look for {company}? Book a demo →"),
    "website": ("{headline}.\n{claims}\n"
                "See the full ROI breakdown for {company}. Start your assessment →"),
}


def _join_claims(claim_ids: list[str]) -> str:
    markers = [f"[[{c}]]" for c in claim_ids]
    if len(markers) == 1:
        body = markers[0]
    elif len(markers) == 2:
        body = f"{markers[0]} and {markers[1]}"
    else:
        body = ", ".join(markers[:-1]) + f", and {markers[-1]}"
    return f"Helix Analytics {body}."


def _role_of(segment: str) -> str:
    return segment.split("__")[0]


def build_variants(channel: str = "email") -> dict[str, list[Variant]]:
    tmpl = CHANNEL_TEMPLATES[channel]
    out: dict[str, list[Variant]] = {}
    for seg in ALL_SEGMENTS:
        role = _role_of(seg)
        variants = []
        for arm, angle, headline, claim_ids in ROLE_ANGLES[role] + [LIE_ANGLE]:
            claims_clause = _join_claims(claim_ids)
            template = tmpl.format(name="{name}", company="{company}",
                                   headline=headline, claims=claims_clause)
            variants.append(Variant(
                variant_id=f"{seg}__{channel}__{arm}", segment=seg, channel=channel,
                arm_label=arm, template=template, claim_ids=claim_ids,
                planted_lie=(arm == "LIE"), headline=headline))
        out[seg] = variants
    return out


def build_action_pool(gate, channel: str, campaign: str, constrained: bool = True):
    """Gate every variant's claims once (claim-level cache -> not per user) and add the
    cleared ones to the action pool. constrained=False keeps blocked variants in the pool
    — the unconstrained twin used to prove the bandit *would* pick the lie if allowed.
    Returns (ActionPool, clearance_report)."""
    from pipeline.common.store import ActionPool

    pool = ActionPool(campaign, channel)
    report: list[dict] = []
    for seg, variants in build_variants(channel).items():
        for v in variants:
            verdicts = gate.verify_variant(v)
            cleared = all(cv.verdict.value != "red" for cv in verdicts)
            if cleared or not constrained:
                pool.add(seg, v.variant_id)
            report.append({
                "variant_id": v.variant_id, "segment": seg, "arm": v.arm_label,
                "planted_lie": v.planted_lie, "cleared": cleared,
                "in_pool": cleared or not constrained,
                "verdicts": [{"claim_id": cv.claim_id, "verdict": cv.verdict.value,
                              "flags": cv.rule_flags} for cv in verdicts],
            })
    return pool, report
