"""The Gate — core verdicts, claim-level caching, and headline properties T2 + T3.

These hit the real Gate (no mocks). Seed-locked and deterministic.
"""
from __future__ import annotations

from pipeline.common.schemas import Verdict
from pipeline.library import seed_data


# --- core ------------------------------------------------------------------
def test_green_amber_red(gate, library):
    assert gate.verify_claim(library.claim("c_soc2").text, library.claim("c_soc2")).verdict == Verdict.GREEN
    assert gate.verify_claim(library.claim("c_tco").text, library.claim("c_tco")).verdict == Verdict.AMBER
    assert gate.verify_claim(seed_data.PLANTED_LIE_TEXT, None).verdict == Verdict.RED


def test_claim_is_gated_once(gate, library):
    c = library.claim("c_soc2")
    gate.verify_claim(c.text, c)
    n = gate.compute_calls
    gate.verify_claim(c.text, c)          # same (claim, source_version, rules_version)
    assert gate.compute_calls == n        # served from the verdict cache


# --- T2: the legal-hold flip, attributable to rules_version alone ----------
def test_legal_hold_flip_blocks_only_via_rules(gate, library, rules):
    tco = library.claim("c_tco")
    before = gate.verify_claim(tco.text, tco)
    assert before.verdict == Verdict.AMBER          # sendable with a disclaimer, hold off

    rules.set_hold("mlr_hold_tco", True)            # legal flips the hold
    after = gate.verify_claim(tco.text, tco)
    assert after.verdict == Verdict.RED
    assert "mlr_hold_tco" in after.rule_flags

    # the ONLY thing that changed is rules_version — same claim text, same source_version
    assert before.text == after.text
    assert before.source_version == after.source_version
    assert before.rules_version != after.rules_version


# --- T3: drift re-verifies EXACTLY the affected claims, nothing else --------
def test_drift_is_surgical(gate, library):
    for c in library.claims_in_date():              # warm every claim
        gate.verify_claim(c.text, c)
    seen = set(gate.verified_keys)
    snapshot = {c.claim_id: gate.verify_claim(c.text, c).model_dump()
                for c in library.claims_in_date()}

    library.apply_source_change(
        "s_pricing",
        "Helix Analytics is priced at $0.15 per patient record. "
        "There is no implementation fee for systems under 200 beds.")

    for c in library.claims_in_date():              # re-verify everything
        gate.verify_claim(c.text, c)
    recomputed = {k[0] for k in gate.verified_keys if k not in seen}

    # no over-invalidation and no under-invalidation
    assert recomputed == {"c_price", "c_nofee"}

    # every unaffected claim's verdict is byte-identical (served from cache)
    for cid, snap in snapshot.items():
        if cid in recomputed:
            continue
        assert gate.verify_claim(library.claim(cid).text, library.claim(cid)).model_dump() == snap

    # the stale-priced claim flips red; the unchanged one does not
    assert gate.verify_claim(library.claim("c_price").text, library.claim("c_price")).verdict == Verdict.RED
    assert gate.verify_claim(library.claim("c_nofee").text, library.claim("c_nofee")).verdict != Verdict.RED
