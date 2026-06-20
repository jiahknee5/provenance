"""Produce the Observatory's recorded run — the deterministic seeded replay (decision R5).

Runs the REAL pipeline with the observability recorder attached, so every node's
INPUT / TOOL / DECISION / OUTPUT lands in data/demo/observe/<lane>.jsonl, then derives the
three read artifacts the dashboard serves:

    topology.json   — the node graph + tooling + edges (from pipeline/common/topology.py)
    node_evals.json — per node: its tools, its I/O contract, and every event it emitted
                      (the operator can step the input→decision→output of each node)
    meta.json       — phase ribbon, lane legend, profile/seed, and the P1-P5 verdicts
                      derived from the run's own artifacts (a signal that can go red)

The JSONL ledger is byte-identical across runs (seq restarts at 0; `t` is a logical clock).
`pytest` remains the authoritative gate for P1-P5; meta.json mirrors them onto the surface.

Run:  python -m scripts.trace
"""
from __future__ import annotations

import json
from collections import defaultdict

from datetime import datetime, timezone

from pipeline.common import observe, topology
from pipeline.common.config import (OBSERVE_DIR, RUNS_DIR, DATA_DIR, INFERENCE_PROFILE,
                                    SEED, ENRICH_MODE)
from pipeline.common.schemas import Recipient
from pipeline.evals.golden import run_golden
from pipeline.library.library import ClaimsLibrary
from scripts.pipeline import run_all

EVAL_HISTORY = DATA_DIR / "eval_history.jsonl"


def _load(name: str, default=None):
    p = RUNS_DIR / name
    return json.loads(p.read_text()) if p.exists() else default


def run_enrichment_demo() -> dict:
    """The per-recipient enrichment touchpoint (T2 enrich → T3 personalize → T4 fact audit),
    recorded on the enrichment lane. Deterministic in the default synthetic mode; in live
    mode the news fact is real but cached, so replays stay deterministic."""
    from pipeline.enrichment.gate import EnrichmentGate
    from pipeline.enrichment.engine import enrich, personalize
    from pipeline.enrichment.audit import run_fact_audit
    from pipeline.enrichment.store import ProfileStore
    from pipeline.generation.variants import build_variants

    maria = Recipient(
        recipient_id="r_demo_maria", token="demo000000000000", name="Maria Chen",
        email="maria.chen@northwindhealth.org", company="Northwind Health",
        role="clinops", company_size="idn", region="Midwest",
        use_case="reduce length of stay", urgency="high", consent=True,
        heard_via="webinar", segment="clinops__ent", created_at="2025-01-01T00:00:00Z")

    gate = EnrichmentGate()
    store = ProfileStore()
    lib = ClaimsLibrary.from_seed()

    observe.set_phase("T2 · Enrich")
    profile = enrich(maria, gate=gate, store=store)   # mode = config default

    observe.set_phase("T3 · Personalize")
    variant = build_variants("email")[maria.segment][0]   # arm A (verified claims)
    claim_body = variant.render(maria, lib.claim_text_map())
    pers = personalize(maria, profile, claim_body)

    observe.set_phase("T4 · Fact audit")
    audit = run_fact_audit(gate, maria)

    demo = {
        "recipient": {"id": maria.recipient_id, "name": maria.name, "company": maria.company,
                      "segment": maria.segment, "consent": maria.consent},
        "mode": ENRICH_MODE, "signals": profile.signals,
        "usable": len(profile.usable_facts), "blocked": len(profile.blocked_facts),
        "facts": [f.model_dump(mode="json") for f in profile.facts],
        "rendered": pers["body"], "personalization": pers["personalization"],
        "fact_audit": audit, "profiles_db": store.summary(),
    }
    (OBSERVE_DIR / "enrichment.json").write_text(json.dumps(demo, indent=2, default=str))
    return demo


def _properties(enrich_demo: dict | None = None) -> dict:
    """The 5 headline properties + E1 (enrichment), checked against the run's OWN artifacts."""
    c1 = _load("campaign_c1_email.json", {})
    twin = _load("campaign_twin_email.json", {})
    c2 = _load("campaign_c2_email.json", {})
    drift = _load("drift_campaign_transition.json", {})
    assurance = _load("assurance.json", {})
    ledgers = _load("ledgers.json", {})

    P: dict = {}

    p1 = c1.get("selections_of_lie", -1) == 0 and not c1.get("winner_is_lie_anywhere", True)
    P["P1"] = {"pass": bool(p1), "node": "bandit",
               "detail": f"constrained bandit selected the lie {c1.get('selections_of_lie')}× "
                         f"(twin {twin.get('selections_of_lie')}×) across {c1.get('n')} sends"}

    before, after = drift.get("before", {}), drift.get("after", {})
    affected = drift.get("affected_claims", [])
    held = affected[0] if affected else None
    p2 = bool(held) and after.get(held) == "red" and before.get(held) != "red"
    P["P2"] = {"pass": bool(p2), "node": "rules",
               "detail": f"{held}: {before.get(held)}→{after.get(held)} the instant the MLR hold flipped"}

    recomputed = sorted(drift.get("recomputed_ids", []))
    p3 = recomputed == sorted(affected) and len(recomputed) > 0
    P["P3"] = {"pass": bool(p3), "node": "drift",
               "detail": f"re-verified exactly {recomputed} (== affected {sorted(affected)}), no over/under-invalidation"}

    mism = []
    reds = 0
    for seg, L in ledgers.items():
        if seg == "_spotlight" or not isinstance(L, dict):
            continue
        ev = {c["claim_id"]: c["verdict"] for c in L.get("email", {}).get("claims", [])}
        wv = {c["claim_id"]: c["verdict"] for c in L.get("website", {}).get("claims", [])}
        reds += sum(1 for c in L.get("website", {}).get("claims", []) if c["verdict"] == "red")
        for cid in set(ev) & set(wv):
            if ev[cid] != wv[cid]:
                mism.append(f"{seg}:{cid}")
    p4 = not mism and reds == 0
    P["P4"] = {"pass": bool(p4), "node": "website",
               "detail": "same claim_id → same verdict on email & website; 0 red claims rendered"
                         + (f"; MISMATCH {mism}" if mism else "")}

    g = assurance.get("gate", {}).get("catch_rate", 0.0)
    b = assurance.get("baseline", {}).get("catch_rate", 0.0)
    fr = assurance.get("gate", {}).get("false_reject", 1.0)
    bfr = assurance.get("baseline", {}).get("false_reject", 0.0)
    p5 = g > b and fr <= bfr + 1e-9
    P["P5"] = {"pass": bool(p5), "node": "assurance",
               "detail": f"Gate catch {g*100:.0f}% > single-judge {b*100:.0f}% at "
                         f"{fr*100:.0f}% false-reject (baseline {bfr*100:.0f}%)"}

    # E1 — enrichment fact-gate (new acceptance property for the enrichment feature)
    if enrich_demo:
        fa = enrich_demo.get("fact_audit", {})
        e1 = fa.get("catch_rate", 0.0) >= 1.0 and fa.get("false_block", 1.0) == 0.0
        P["E1"] = {"pass": bool(e1), "node": "enrich_gate",
                   "detail": f"fact-gate blocked {fa.get('catch_rate', 0)*100:.0f}% of un-shippable facts "
                             f"(disallowed/stale/PHI/non-consent) at {fa.get('false_block', 0)*100:.0f}% false-block; "
                             f"{enrich_demo.get('blocked', 0)} blocked fact(s) withheld from copy"}

    # the warm-start dividend (context, not a pillar)
    P["_warm_start"] = {"pass": c2.get("final_regret", 9e9) <= c1.get("final_regret", 0),
                        "detail": f"Campaign 2 regret {c2.get('final_regret')} ≤ Campaign 1 {c1.get('final_regret')}"}
    return P


def _read_ledger() -> list[dict]:
    events: list[dict] = []
    for p in sorted(OBSERVE_DIR.glob("*.jsonl")):
        for line in p.read_text().splitlines():
            if line.strip():
                events.append(json.loads(line))
    events.sort(key=lambda e: e["seq"])
    return events


def _exemplar(evs: list[dict]) -> dict | None:
    """The most illustrative event for a node — richest I/O, prefer a RED/LIE/veto moment."""
    def score(e):
        rich = sum(1 for k in ("input", "decision", "output") if k in e)
        flavour = 2 if any(w in e.get("detail", "").upper() for w in ("RED", "LIE", "VETO", "BLOCK")) else 0
        return rich + flavour
    return max(evs, key=score) if evs else None


def derive_artifacts(summary: dict, enrich_demo: dict | None = None) -> dict:
    topo = topology.topology()
    (OBSERVE_DIR / "topology.json").write_text(json.dumps(topo, indent=2))

    events = _read_ledger()
    by_node: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        by_node[e.get("node", e["lane"])].append(e)

    props = _properties(enrich_demo)
    node_evals = []
    for n in topo["nodes"]:
        evs = by_node.get(n["id"], [])
        computed = [e for e in evs if e["event"] != "CACHE_HIT"]
        served = len(evs) - len(computed)
        node_evals.append({
            **{k: n[k] for k in ("id", "lane", "label", "tools", "input", "decision",
                                 "output", "code", "property")},
            "n_events": len(evs), "n_computed": len(computed), "served_from_cache": served,
            "events": computed[:15], "exemplar": _exemplar(computed),
        })
    (OBSERVE_DIR / "node_evals.json").write_text(
        json.dumps({"nodes": node_evals, "properties": props}, indent=2, default=str))

    def _is_headline(k):           # P1..P5 only — E1/_warm_start tracked but not in the headline count
        return len(k) >= 2 and k[0] == "P" and k[1:].isdigit()

    meta = {
        "run_id": "provenance-demo",
        "profile": INFERENCE_PROFILE, "seed": SEED, "offline": True, "cost_usd": 0.0,
        "enrich_mode": ENRICH_MODE,
        "phases": topo["phases"], "lanes": topo["lanes"],
        "node_count": len(topo["nodes"]), "total_events": len(events),
        "properties": props,
        "properties_pass": sum(1 for k, v in props.items() if _is_headline(k) and v["pass"]),
        "properties_total": sum(1 for k in props if _is_headline(k)),
        "summary": summary,
        "enrichment": enrich_demo,
        "determinism": "byte-identical re-run (seq restarts at 0; logical clock); pytest is the authoritative gate",
    }
    (OBSERVE_DIR / "meta.json").write_text(json.dumps(meta, indent=2, default=str))
    return meta


def _append_history(meta: dict, golden: dict) -> None:
    """Append this run's assurance metrics to the over-time history (a regression detector).
    Lives outside observe/ so it never breaks the byte-identical ledger hash; wall-clock ts
    is fine here (it IS the time axis)."""
    a = _load("assurance.json", {})
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "golden_passed": golden["summary"]["passed"], "golden_total": golden["summary"]["total"],
        "lifecycle_pass": golden["lifecycle"]["pass"],
        "gate_catch": a.get("gate", {}).get("catch_rate"),
        "baseline_catch": a.get("baseline", {}).get("catch_rate"),
        "false_reject": a.get("gate", {}).get("false_reject"),
        "ece": a.get("ece"),
        "e1_catch": (meta.get("enrichment") or {}).get("fact_audit", {}).get("catch_rate"),
        "props_pass": meta["properties_pass"], "props_total": meta["properties_total"],
    }
    with open(EVAL_HISTORY, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, default=str) + "\n")


def main() -> dict:
    observe.start_run("provenance-demo", topology.PHASES)
    summary = run_all()
    enrich_demo = run_enrichment_demo()
    observe.end_run(summary)

    # golden evals (node-level fresh captures + workflow-level scored from the ledger)
    golden = run_golden(_read_ledger())
    (OBSERVE_DIR / "golden_evals.json").write_text(json.dumps(golden, indent=2, default=str))

    # funnel scenarios (customer journeys + surface-policy views) for the funnel dashboard
    from pipeline.customer.scenarios import report as funnel_report
    (OBSERVE_DIR / "funnel.json").write_text(json.dumps(funnel_report(), indent=2, default=str))

    meta = derive_artifacts(summary, enrich_demo)
    _append_history(meta, golden)

    print(f"traced {meta['total_events']} events across {len(meta['lanes'])} lanes · "
          f"P1-P5 {meta['properties_pass']}/{meta['properties_total']} pass · "
          f"golden {golden['summary']['passed']}/{golden['summary']['total']} · "
          f"lifecycle {'✓' if golden['lifecycle']['pass'] else '✗'} · "
          f"enrich={meta['enrich_mode']} · $0 offline")
    for k, v in meta["properties"].items():
        if not k.startswith("_"):
            print(f"  {'✓' if v['pass'] else '✗'} {k}: {v['detail']}")
    return meta


if __name__ == "__main__":
    main()
