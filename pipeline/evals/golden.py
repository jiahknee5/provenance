"""Golden evals — the canonical input→expected suite for every Provenance step.

Each case is a row: INPUT → GRAPH LOG (a subtable of node/tool → input → decision/output)
→ OUTPUT, scored against its golden expectation. Node-level steps (the Gate, the Enrichment
Gate) are run *fresh* here with an isolated verdict cache so every case computes (and emits
its full graph log); workflow-level steps (Optimizer, Drift, Assurance, Website) are scored
from the run's own artifacts with their graph log pulled from the recorded ledger.

Plus one overarching lifecycle eval (Maria, end to end) in the same format.

These are real tests: `tests/test_golden_evals.py` asserts the whole suite passes.
"""
from __future__ import annotations

import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path

from pipeline.common import db, observe
from pipeline.common.cache import LLMCache, VerdictCache
from pipeline.common.config import RUNS_DIR
from pipeline.common.schemas import Recipient
from pipeline.enrichment.engine import enrich, personalize
from pipeline.enrichment.gate import EnrichmentGate
from pipeline.enrichment.schemas import RawFact
from pipeline.gate.gate import Gate
from pipeline.gate.rules import RulesEngine
from pipeline.generation.variants import build_variants
from pipeline.library.library import ClaimsLibrary

MARIA = Recipient(
    recipient_id="r_eval_maria", token="eval000000000000", name="Maria Chen",
    email="maria.chen@northwindhealth.org", company="Northwind Health",
    role="clinops", company_size="idn", region="Midwest",
    use_case="reduce length of stay", urgency="high", consent=True,
    heard_via="webinar", segment="clinops__ent", created_at="2025-01-01T00:00:00Z")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _fresh_gate(lib: ClaimsLibrary, rules: RulesEngine) -> Gate:
    """A Gate with an isolated cache so every golden case computes (full graph log)."""
    fd, p = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    db.init_db(Path(p))
    conn = db.connect(Path(p))
    return Gate(lib, rules, verdict_cache=VerdictCache(conn=conn), llm_cache=LLMCache(conn=conn))


def _graph_log(events: list[dict]) -> list[dict]:
    """Normalize captured/ledger events into the graph-log subtable rows."""
    rows = []
    for e in events:
        if e.get("event") in ("RUN_START", "RUN_END", "PHASE"):
            continue
        rows.append({"node": e.get("node", e.get("lane", "")), "tool": e.get("tool", ""),
                     "event": e.get("event", ""), "detail": e.get("detail", ""),
                     "input": e.get("input"), "decision": e.get("decision"),
                     "output": e.get("output")})
    return rows


def _load(name: str, default=None):
    p = RUNS_DIR / name
    return json.loads(p.read_text()) if p.exists() else default


def _case(name, inp, graph_log, output, expected, ok):
    return {"name": name, "input": inp, "graph_log": graph_log, "output": output,
            "expected": expected, "pass": bool(ok)}


# --------------------------------------------------------------------------- #
# Gate — node-level golden cases (run fresh, captured)
# --------------------------------------------------------------------------- #
def _gate_cases(lib: ClaimsLibrary) -> dict:
    rules = RulesEngine.load()
    rules_hold = RulesEngine.load()
    rules_hold.set_hold("mlr_hold_tco", True)
    gate = _fresh_gate(lib, rules)
    gate_hold = _fresh_gate(lib, rules_hold)

    # (name, claim_id | free text, use_hold_gate, expected_verdict)
    specs = [
        ("Supported security claim → GREEN", "c_soc2", False, "green"),
        ("Clinical-outcome claim needs a disclaimer → AMBER", "c_los", False, "amber"),
        ("ROI claim needs a disclaimer → AMBER", "c_tco", False, "amber"),
        ("ROI claim under the MLR legal hold → RED", "c_tco", True, "red"),
        ("Number drifted 47%→57% → RED (numeric veto)",
         "free:Helix Analytics cuts total cost of ownership by 57%", False, "red"),
        ("Unsupported superlative (#1) → RED",
         "free:Helix Analytics is the #1 best-in-class platform", False, "red"),
        ("Guaranteed outcome (the planted lie) → RED",
         "free:Helix Analytics guarantees a 60% reduction in hospital readmissions", False, "red"),
    ]
    cases = []
    for name, ref, use_hold, expect in specs:
        g = gate_hold if use_hold else gate
        if ref.startswith("free:"):
            text, claim, cid = ref[5:], None, "(free)"
        else:
            claim = lib.claim(ref)
            text, cid = claim.text, ref
        observe.start_capture()
        cv = g.verify_claim(text, claim)
        evs = observe.stop_capture()
        out = {"verdict": cv.verdict.value, "confidence": cv.confidence, "flags": cv.rule_flags}
        cases.append(_case(name,
                           {"claim_id": cid, "text": text, "legal_hold": use_hold},
                           _graph_log(evs), out, {"verdict": expect},
                           cv.verdict.value == expect))
    return {"step": "gate", "label": "The Gate — claim verification", "cases": cases}


# --------------------------------------------------------------------------- #
# Enrichment Gate — node-level fact cases (run fresh, captured)
# --------------------------------------------------------------------------- #
def _enrichment_cases() -> dict:
    egate = EnrichmentGate()
    no_consent = MARIA.model_copy(update={"consent": False})
    specs = [
        ("Clean consented fact → USABLE",
         RawFact(key="recent_news", value="opened a regional facility", source="company_news_rss"),
         MARIA, "usable"),
        ("Disallowed source (scraped) → BLOCKED",
         RawFact(key="seniority", value="VP", source="scraped_linkedin"), MARIA, "blocked"),
        ("Stale fact past its TTL → BLOCKED",
         RawFact(key="recent_news", value="old", source="company_news_rss", age_seconds=10_000_000),
         MARIA, "blocked"),
        ("PHI key → BLOCKED",
         RawFact(key="diagnosis", value="redacted", source="firmographic_sim"), MARIA, "blocked"),
        ("Recipient never consented → BLOCKED",
         RawFact(key="intent_topic", value="ROI", source="intent_sim"), no_consent, "blocked"),
    ]
    cases = []
    for name, fact, recip, expect in specs:
        observe.start_capture()
        pf = egate.evaluate(fact, recip)
        evs = observe.stop_capture()
        out = {"verdict": pf.verdict.value, "basis": pf.basis, "reasons": pf.reasons}
        cases.append(_case(name,
                           {"key": fact.key, "value": fact.value, "source": fact.source,
                            "age_seconds": fact.age_seconds, "consent": recip.consent},
                           _graph_log(evs), out, {"verdict": expect},
                           pf.verdict.value == expect))
    return {"step": "enrich_gate", "label": "The Enrichment Gate — fact verification", "cases": cases}


# --------------------------------------------------------------------------- #
# Library — node-level (synthesized graph log from the claim-evidence graph)
# --------------------------------------------------------------------------- #
def _library_case(lib: ClaimsLibrary) -> dict:
    glog = []
    all_bound = True
    for cid, c in lib.claims.items():
        src = lib.source(c.source_id)
        bound = src.text[c.span[0]:c.span[1]]
        ok = bool(bound) and c.span[1] > c.span[0]
        all_bound = all_bound and ok
        glog.append({"node": "bind", "tool": "claim→evidence graph", "event": "OUTPUT",
                     "detail": f"{cid} ← {c.source_id}", "input": {"claim_id": cid},
                     "output": {"span": list(c.span), "evidence": bound}})
    ok = len(lib.claims) == 10 and all_bound
    case = _case("4 sources → 10 atomic claims, each span-bound",
                 {"sources": sorted(lib.sources), "library_version": lib.library_version()},
                 glog, {"claims": len(lib.claims), "all_span_bound": all_bound},
                 {"claims": 10, "all_span_bound": True}, ok)
    return {"step": "library", "label": "Claims Library", "cases": [case]}


# --------------------------------------------------------------------------- #
# Workflow-level steps — scored from run artifacts, graph log from the ledger
# --------------------------------------------------------------------------- #
def _by_lane(ledger: list[dict]) -> dict:
    out = defaultdict(list)
    for e in ledger:
        out[e.get("lane", "")].append(e)
    return out


def _workflow_cases(ledger: list[dict]) -> list[dict]:
    lanes = _by_lane(ledger)
    steps = []

    # Optimizer (P1)
    c1, twin = _load("campaign_c1_email.json", {}), _load("campaign_twin_email.json", {})
    ok = c1.get("selections_of_lie", -1) == 0 and not c1.get("winner_is_lie_anywhere", True)
    steps.append({"step": "optimizer", "label": "Optimizer — bandit over verified arms", "cases": [
        _case("A Gate-blocked lie can never be selected (twin converges to it)",
              {"recipients": c1.get("n"), "constrained": True},
              _graph_log([e for e in lanes.get("optimizer", []) if e.get("event") in ("INPUT", "DECISION", "OUTPUT")][:14]),
              {"constrained_lie_selections": c1.get("selections_of_lie"),
               "twin_lie_selections": twin.get("selections_of_lie")},
              {"constrained_lie_selections": 0}, ok)]})

    # Drift (P2/P3)
    drift = _load("drift_campaign_transition.json", {})
    after, before = drift.get("after", {}), drift.get("before", {})
    affected = drift.get("affected_claims", [])
    recomputed = sorted(drift.get("recomputed_ids", []))
    ok = bool(affected) and after.get(affected[0]) == "red" and recomputed == sorted(affected)
    steps.append({"step": "drift", "label": "Drift Monitor — surgical re-verify", "cases": [
        _case("Legal-hold flip re-verifies exactly the held claim → RED",
              {"event": drift.get("event"), "change": drift.get("change")},
              _graph_log(lanes.get("drift", [])),
              {"before": before, "after": after, "recomputed": recomputed},
              {"after_red": True, "recomputed_equals_affected": True}, ok)]})

    # Assurance (P5)
    a = _load("assurance.json", {})
    g, b = a.get("gate", {}).get("catch_rate", 0.0), a.get("baseline", {}).get("catch_rate", 0.0)
    fr = a.get("gate", {}).get("false_reject", 1.0)
    ok = g > b
    steps.append({"step": "assurance", "label": "Assurance Lab — Gate vs single judge", "cases": [
        _case("Gate catch-rate > single-judge baseline at fixed false-reject",
              {"n_traps": a.get("n_traps"), "n_clean": a.get("n_clean")},
              _graph_log(lanes.get("assurance", [])),
              {"gate_catch": g, "baseline_catch": b, "false_reject": fr, "ece": a.get("ece")},
              {"gate_catch_gt_baseline": True}, ok)]})

    # Website (P4)
    ledgers = _load("ledgers.json", {})
    mism, reds = [], 0
    for seg, L in ledgers.items():
        if seg == "_spotlight" or not isinstance(L, dict):
            continue
        ev = {c["claim_id"]: c["verdict"] for c in L.get("email", {}).get("claims", [])}
        wv = {c["claim_id"]: c["verdict"] for c in L.get("website", {}).get("claims", [])}
        reds += sum(1 for c in L.get("website", {}).get("claims", []) if c["verdict"] == "red")
        mism += [f"{seg}:{cid}" for cid in set(ev) & set(wv) if ev[cid] != wv[cid]]
    ok = not mism and reds == 0
    steps.append({"step": "website", "label": "Website channel — same Gate, both channels", "cases": [
        _case("Same claim_id → same verdict on email & website; 0 red rendered",
              {"segments": len([s for s in ledgers if s != "_spotlight"])},
              _graph_log([e for e in lanes.get("website", []) if e.get("event") in ("INPUT", "DECISION", "OUTPUT")][:12]),
              {"verdict_mismatches": mism, "red_claims_rendered": reds},
              {"verdict_mismatches": [], "red_claims_rendered": 0}, ok)]})
    return steps


# --------------------------------------------------------------------------- #
# Overarching lifecycle eval (Maria, end to end) — same format
# --------------------------------------------------------------------------- #
def lifecycle_eval(lib: ClaimsLibrary) -> dict:
    rules = RulesEngine.load()
    gate = _fresh_gate(lib, rules)
    egate = EnrichmentGate()

    observe.start_capture()
    profile = enrich(MARIA, gate=egate)                       # T2 enrich + gate facts
    variant = build_variants("email")[MARIA.segment][0]       # the verified-claim variant
    verdicts = [gate.verify_claim(lib.claim(c).text, lib.claim(c)) for c in variant.claim_ids]
    claim_body = variant.render(MARIA, lib.claim_text_map())
    pers = personalize(MARIA, profile, claim_body)            # T3 personalize (gated facts)
    evs = observe.stop_capture()

    cleared = all(v.verdict.value != "red" for v in verdicts)
    facts_have_basis = all(r["basis"] for r in pers["personalization"])
    no_blocked_in_copy = all(
        bf.value not in pers["body"] for bf in profile.blocked_facts) if profile.blocked_facts else True
    checks = [
        {"name": "every shown product claim cleared the Gate (no RED)", "pass": cleared},
        {"name": "every inlined personal fact carries a lawful basis", "pass": facts_have_basis},
        {"name": "no blocked fact reached the copy", "pass": no_blocked_in_copy},
    ]
    ok = all(c["pass"] for c in checks)
    return {
        "name": "Maria Chen — form → enrich → Gate → personalize (end to end)",
        "input": {"recipient": MARIA.company, "segment": MARIA.segment, "consent": MARIA.consent},
        "graph_log": _graph_log(evs),
        "output": {
            "verified_claims": [{"claim_id": v.claim_id, "verdict": v.verdict.value} for v in verdicts],
            "usable_facts": len(profile.usable_facts), "blocked_facts": len(profile.blocked_facts),
            "inlined": [r["key"] for r in pers["personalization"]],
        },
        "checks": checks, "pass": ok,
    }


# --------------------------------------------------------------------------- #
# assemble
# --------------------------------------------------------------------------- #
def run_golden(ledger: list[dict] | None = None) -> dict:
    lib = ClaimsLibrary.from_seed()
    ledger = ledger or []
    steps = [_library_case(lib), _gate_cases(lib), _enrichment_cases()] + _workflow_cases(ledger)
    total = sum(len(s["cases"]) for s in steps)
    passed = sum(1 for s in steps for c in s["cases"] if c["pass"])
    return {"steps": steps, "summary": {"passed": passed, "total": total},
            "lifecycle": lifecycle_eval(lib)}
