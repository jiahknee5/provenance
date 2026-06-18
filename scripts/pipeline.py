"""The full Provenance demo pipeline — deterministic, end to end.

  form data (1000) -> Claims Library + Gate (verify) -> Campaign 1 (bandit over verified
  arms, simulated CTA) + unconstrained twin -> learnings -> anti-drift (legal hold flips)
  -> Campaign 2 (warm-started, post-drift) -> ultra-personalized website (same Gate, CTA)
  -> Assurance Lab (per channel).

Run:  python -m scripts.pipeline           # everything, prints a summary
Every artifact lands in data/demo/runs/ for the inspector and is reproducible from SEED.
"""
from __future__ import annotations

import json

from pipeline.common import db, observe
from pipeline.common.config import RUNS_DIR
from pipeline.common.manifest import RunManifest
from pipeline.common.store import PosteriorStore
from pipeline.drift.monitor import DriftMonitor
from pipeline.gate.gate import Gate
from pipeline.gate.rules import RulesEngine
from pipeline.generation import recipients
from pipeline.generation.variants import build_action_pool, build_variants
from pipeline.library.library import ClaimsLibrary
from pipeline.optimizer.campaign import run_campaign
from pipeline.assurance.harness import run_per_channel

CAMPAIGN_SEED = 100


def _ledger_for(gate, library, r, seg, channel, arm):
    v = next((x for x in build_variants(channel)[seg] if x.arm_label == arm),
             build_variants(channel)[seg][0])
    claims = []
    for cid in v.claim_ids:
        node = library.claim(cid)
        cv = gate.verify_claim(node.text, node)
        claims.append({"claim_id": cid, "text": f"Helix Analytics {node.text}",
                       "verdict": cv.verdict.value, "confidence": cv.confidence,
                       "source": library.source(node.source_id).title, "flags": cv.rule_flags})
    return {"variant_id": v.variant_id, "arm": v.arm_label, "headline": v.headline,
            "body": v.render(r, library.claim_text_map()), "claims": claims}


def _sample_ledgers(gate, library, recips, email_winners, web_winners) -> dict:
    """One representative email + website ledger per segment, plus a drift spotlight (the
    ROI variant the legal hold just blocked — shows a red claim light)."""
    out = {}
    by_seg = {}
    for r in recips:
        by_seg.setdefault(r.segment, r)
    for seg, r in by_seg.items():
        out[seg] = {
            "recipient": r.name, "company": r.company, "role": r.role,
            "email": _ledger_for(gate, library, r, seg, "email",
                                 email_winners.get(seg, f"{seg}__email__A").split("__")[-1]),
            "website": _ledger_for(gate, library, r, seg, "website",
                                   web_winners.get(seg, f"{seg}__website__A").split("__")[-1]),
        }
    cfo_r = by_seg.get("cfo__core")
    if cfo_r:
        out["_spotlight"] = {"recipient": cfo_r.name, "company": cfo_r.company,
                             "note": "The ROI variant (A) that won Campaign 1 — now blocked by the MLR hold.",
                             "email": _ledger_for(gate, library, cfo_r, "cfo__core", "email", "A")}
    return out


def run_all() -> dict:
    db.reset_db()
    observe.set_phase("P1 · Library")
    lib = ClaimsLibrary.from_seed()
    rules = RulesEngine.load()
    gate = Gate(lib, rules)
    recips = recipients.generate(1000)
    recipients.save(recips)
    lib.save()
    observe.emit("library", "OUTPUT", node="library",
                 tool="claim→evidence graph · content-hash versioning",
                 detail=f"{len(lib.sources)} sources → {len(lib.claims)} atomic claims "
                        f"(library {lib.library_version()})",
                 input={"sources": sorted(lib.sources), "library_version": lib.library_version()},
                 output={"claims": sorted(lib.claims),
                         "claim_text": {cid: c.text for cid, c in lib.claims.items()}})

    # --- Campaign 1: email, constrained, + the unconstrained twin (the proof) ---
    observe.set_phase("P2 · Gate")
    pool1, report1 = build_action_pool(gate, "email", "c1", constrained=True)
    observe.set_phase("P3 · Campaign 1")
    post1 = PosteriorStore("c1", "email")
    t1 = run_campaign("email", "c1", recips, pool1, post1, constrained=True, seed=CAMPAIGN_SEED)
    observe.set_phase("P4 · Twin")
    pool1u, _ = build_action_pool(gate, "email", "twin", constrained=False)
    t1u = run_campaign("email", "twin", recips, pool1u, PosteriorStore("twin", "email"),
                       constrained=False, seed=CAMPAIGN_SEED)
    (RUNS_DIR / "pool_report.json").write_text(json.dumps(report1, indent=2))
    email_winners = {seg: s["winner"] for seg, s in t1["per_segment"].items()}

    # --- Anti-drift agent: legal hold flips between campaigns ---
    observe.set_phase("P5 · Drift")
    drift = DriftMonitor(gate, lib, rules).fire_legal_hold(
        "mlr_hold_tco", True, [pool1], name="campaign_transition")
    (RUNS_DIR / "demo_state.json").write_text(json.dumps({"hold": True}, indent=2))

    # --- Campaign 2: email, warm-started from C1, on the post-drift truth boundary ---
    observe.set_phase("P6 · Campaign 2")
    post2 = PosteriorStore("c2", "email")
    post2.warm_start_from(post1)
    pool2, _ = build_action_pool(gate, "email", "c2", constrained=True)
    t2 = run_campaign("email", "c2", recips, pool2, post2, constrained=True, seed=CAMPAIGN_SEED + 1)
    email_winners.update({seg: s["winner"] for seg, s in t2["per_segment"].items()})

    # --- Website channel: same Gate, transfers learnings, tracks CTA, post-drift ---
    observe.set_phase("P7 · Website")
    poolw, _ = build_action_pool(gate, "website", "web", constrained=True)
    postw = PosteriorStore("web", "website")
    postw.warm_start_from(post2)
    tw = run_campaign("website", "web", recips, poolw, postw, constrained=True, seed=CAMPAIGN_SEED + 2)
    web_winners = {seg: s["winner"] for seg, s in tw["per_segment"].items()}
    (RUNS_DIR / "learnings.json").write_text(json.dumps(web_winners, indent=2))

    # --- Assurance Lab (one harness, sliced per channel) ---
    observe.set_phase("P8 · Assurance")
    assurance = run_per_channel(gate, lib)

    # --- sample ledgers + manifest + summary ---
    (RUNS_DIR / "ledgers.json").write_text(json.dumps(
        _sample_ledgers(gate, lib, recips, email_winners, web_winners), indent=2))
    RunManifest(library_version=lib.library_version(), rules_version=rules.rules_version(),
                notes="run_all").save()

    summary = {
        "recipients": len(recips), "segments": len({r.segment for r in recips}),
        "campaign1": {"lie_selections": t1["selections_of_lie"], "final_regret": t1["final_regret"],
                      "winner_is_lie_anywhere": t1["winner_is_lie_anywhere"]},
        "twin_unconstrained": {"lie_selections": t1u["selections_of_lie"],
                               "segments_won_by_lie": sum(1 for s in t1u["per_segment"].values()
                                                          if s["winner_is_lie"])},
        "drift": {"affected": drift.affected_claims, "recomputed": drift.recomputed_ids,
                  "c_tco": f"{drift.before['c_tco']} -> {drift.after['c_tco']}",
                  "paused": drift.paused_variants},
        "campaign2": {"lie_selections": t2["selections_of_lie"], "final_regret": t2["final_regret"]},
        "website": {"lie_selections": tw["selections_of_lie"]},
        "assurance": {"gate_catch": assurance["gate"]["catch_rate"],
                      "baseline_catch": assurance["baseline"]["catch_rate"],
                      "false_reject": assurance["gate"]["false_reject"],
                      "baseline_number_drift": assurance["baseline"]["by_type"].get("number_drift")},
    }
    (RUNS_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    s = run_all()
    print(json.dumps(s, indent=2))
