"""Headline property T4 — the website renders only Gate-passed claims, and the same
claim carries the same verdict on email and website (one Gate, two channels).
"""
from __future__ import annotations

from app.site import render_site_data
from pipeline.common.schemas import Recipient, Verdict
from pipeline.generation.variants import build_variants


def _cfo_recipient() -> Recipient:
    return Recipient(recipient_id="rt", token="tok", name="Maya Chen", email="m@northwind.org",
                     company="Northwind Health", role="cfo", company_size="community",
                     region="West", use_case="lower total cost of ownership", urgency="high",
                     segment="cfo__core")


def _variant(channel: str, segment: str, arm: str):
    return next(v for v in build_variants(channel)[segment] if v.arm_label == arm)


def test_t4_website_renders_no_red_claim(gate, library, rules):
    rules.set_hold("mlr_hold_tco", True)          # c_tco -> red
    r = _cfo_recipient()
    var_a = _variant("website", "cfo__core", "A")  # uses c_tco
    data = render_site_data(gate, library, r, var_a)

    assert any(c["claim_id"] == "c_tco" for c in data["blocked"])   # it was blocked
    assert all(c["claim_id"] != "c_tco" for c in data["shown"])     # ...and not shown
    tco_text = library.claim("c_tco").text
    assert all(tco_text not in c["text"] for c in data["shown"])    # red text not in the DOM data
    # the page still shows the variant's other, verified claims
    assert {c["claim_id"] for c in data["shown"]} == {"c_deployed", "c_price"}


def test_t4_same_claim_same_verdict_across_channels(gate, library, rules):
    rules.set_hold("mlr_hold_tco", True)
    r = _cfo_recipient()
    web = render_site_data(gate, library, r, _variant("website", "cfo__core", "A"))["ledger"]
    web_verdicts = {c.claim_id: c.verdict for c in web.claims}
    # verify the same claims as they'd appear on the email channel — identical verdicts
    for cid, verdict in web_verdicts.items():
        node = library.claim(cid)
        assert gate.verify_claim(node.text, node).verdict == verdict
    assert web_verdicts["c_tco"] == Verdict.RED
