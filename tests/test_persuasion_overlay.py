"""The persuasion overlay is Gate-bounded — a principle changes the FRAME, never the facts.

Proves: every strategy ships only Gate-cleared claims with sources; a held claim is dropped
(the truth boundary holds for closing copy); no strategy can emit a superlative / comparative
/ named competitor; and strategy selection is deterministic.
"""
from __future__ import annotations

from pipeline.common.schemas import Recipient
from pipeline.personalization import creative as CR
from pipeline.personalization import persuasion
from pipeline.personalization.persuasion import ROLE_PROOF, STRATEGIES


def _rcpt(role="cfo", size="community", urgency="high") -> Recipient:
    return Recipient(recipient_id="p1", token="tok", name="Maya Chen", email="m@northwind.org",
                     company="Northwind Health", role=role, company_size=size, region="West",
                     use_case="lower total cost of ownership", urgency=urgency,
                     segment=f"{role}__{'ent' if size == 'idn' else 'core'}")


def test_every_strategy_ships_only_gate_cleared_claims(gate, library):
    for role in ROLE_PROOF:
        for strat in STRATEGIES:
            plan = persuasion.build_plan(gate, library, _rcpt(role=role), strategy=strat)
            assert plan.claims, f"{role}/{strat} surfaced no claims"
            assert all(c["verdict"] != "red" for c in plan.claims), f"{role}/{strat} shipped a red claim"
            assert all(c["source"] for c in plan.claims), f"{role}/{strat} has a claim with no source"
            assert plan.headline_ok, f"{role}/{strat} headline failed the copy Gate"


def test_legal_hold_drops_the_held_claim(gate, library, rules):
    rules.set_hold("mlr_hold_tco", True)              # c_tco -> red
    plan = persuasion.build_plan(gate, library, _rcpt(role="cfo"), strategy="authority")
    assert "c_tco" in plan.dropped                    # the held claim is dropped...
    assert all(c["claim_id"] != "c_tco" for c in plan.claims)   # ...and never surfaced
    assert plan.claims                                # the plan still has its other provable claims
    assert all(c["verdict"] != "red" for c in plan.claims)


def test_no_strategy_emits_a_superlative_or_competitor(gate, library):
    for strat, spec in STRATEGIES.items():
        checks = CR.verify_copy([spec["headline"], spec["cta"]], facts="",
                                company="Northwind Health", policy="allude",
                                competitors=CR.COMPETITOR_HINTS)
        assert all(c["ok"] for c in checks), f"{strat}: {[c for c in checks if not c['ok']]}"


def test_select_strategy_is_deterministic(gate, library):
    assert persuasion.select_strategy(_rcpt(role="it_security", urgency="low")) == "authority"
    assert persuasion.select_strategy(_rcpt(role="cfo", urgency="high")) == "loss_aversion"
    assert persuasion.select_strategy(_rcpt(role="quality", size="idn", urgency="low")) == "social_proof"
    assert persuasion.select_strategy(_rcpt(role="cfo", urgency="low"), {"abandoned": True}) == "consistency"
    assert persuasion.select_strategy(_rcpt(role="cfo", urgency="low")) == "authority"   # default
    r = _rcpt(role="clinops", urgency="high")
    assert persuasion.select_strategy(r) == persuasion.select_strategy(r)   # stable


def test_unknown_strategy_falls_back_to_selection(gate, library):
    r = _rcpt(role="it_security", urgency="low")
    plan = persuasion.build_plan(gate, library, r, strategy="bogus")
    assert plan.strategy == "authority"               # fell back to select_strategy, didn't crash
