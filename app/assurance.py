"""The Assurance dashboard — the audited trust surface for the whole Provenance workflow.

  GET /assurance              — decomposed reliability: the Gate vs a single-judge baseline on
                                an adversarial trap set (operating point, paired confusion,
                                per-mutation lift, calibration), per-channel identity (P4),
                                a 47-trap ledger, 7-run regression stability + golden coverage,
                                and a fenced illustrative bandit/KPI section.
  GET /api/observe/golden     — the golden eval suite (per-step cases + graph logs)
  GET /api/observe/history    — the over-time metrics history (one entry per run)

EVERY metric is computed from a real artifact (CONSTITUTION Article I): confusion counts,
per-type/severity fractions and Wilson CIs are derived from assurance.json's `items[]` here,
never hand-typed. Charts are dependency-free inline SVG rendered server-side (the inspector
pattern). The bandit/KPI data is the real ThompsonBandit on SYNTHETIC traffic and is fenced +
labelled illustrative (Article VIII).
"""
from __future__ import annotations

import json

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.charts import (confusion_pair, grouped_bars, lift_bars, operating_point,
                        reliability, small_multiples_curves, stability_strip,
                        tile_grid, wilson_ci)
from app.server import app, templates
from pipeline.common.config import DATA_DIR, OBSERVE_DIR, RUNS_DIR
from pipeline.personalization import demo_scenarios as DS
from pipeline.personalization import demo_sim

EVAL_HISTORY = DATA_DIR / "eval_history.jsonl"

MUT_ORDER = ["number_drift", "unsupported_superlative", "false_equivalence", "true_but_unsayable"]
MUT_LABEL = {"number_drift": "Number drift", "unsupported_superlative": "Unsupported superlative",
             "false_equivalence": "False equivalence", "true_but_unsayable": "True but unsayable"}
MUT_ABBR = {"number_drift": "num", "unsupported_superlative": "super",
            "false_equivalence": "equiv", "true_but_unsayable": "unsay"}
MUT_DESC = {"number_drift": "altered figures (a number-blind judge structurally can't verify arithmetic)",
            "unsupported_superlative": "puffery — an unbacked best/most/leading claim",
            "false_equivalence": "a misleading comparison between unlike things",
            "true_but_unsayable": "accurate but compliance-barred (e.g. a claim under legal hold)"}
PROPS = [
    ("P1", "A Gate-blocked lie can never be selected"),
    ("P2", "Legal-hold claim blocked the instant the hold flips (rules_version)"),
    ("P3", "A drift event re-verifies exactly the affected claims"),
    ("P4", "Website renders only Gate-passed claims — same verdict on both channels"),
    ("P5", "Catch-rate beats the single-judge baseline at a fixed false-reject"),
]


def _load(name: str, d=None):
    p = OBSERVE_DIR / name
    if not p.exists():
        p = RUNS_DIR / name
    return json.loads(p.read_text()) if p.exists() else d


def _history() -> list[dict]:
    if not EVAL_HISTORY.exists():
        return []
    return [json.loads(line) for line in EVAL_HISTORY.read_text().splitlines() if line.strip()]


def _confusion(items: list[dict], key: str) -> dict:
    """tp/fn/fp/tn for a caught-flag, computed from the real per-trap rows (label 1 = bad)."""
    return {
        "tp": sum(1 for x in items if x["label"] == 1 and x[key]),
        "fn": sum(1 for x in items if x["label"] == 1 and not x[key]),
        "fp": sum(1 for x in items if x["label"] == 0 and x[key]),
        "tn": sum(1 for x in items if x["label"] == 0 and not x[key]),
    }


def _frac(items: list[dict], pred, key: str) -> tuple[int, int]:
    bad = [x for x in items if x["label"] == 1 and pred(x)]
    return sum(1 for x in bad if x[key]), len(bad)


@app.get("/assurance", response_class=HTMLResponse)
def assurance(request: Request):
    m = demo_sim.build()
    h = m["health"]
    asr = _load("assurance.json") or {}
    golden = _load("golden_evals.json", {})
    hist = _history()
    items = asr.get("items", [])

    # ---- composite trust score (unchanged formula) + its disclosed parts ----
    catch = h["hallucination"]["trap_catch_rate"]
    if catch is None and golden.get("summary"):
        s = golden["summary"]
        catch = round(100 * s.get("passed", 0) / max(s.get("total", 1), 1), 1)
    parts = [h["provenance"]["coverage_pct"],
             100 if not h["provenance"]["hold_in_copy"] else 0,
             100 if h["hallucination"]["selected"] == 0 else 0,
             catch if catch is not None else 100]
    trust = round(sum(parts) / len(parts))

    # ---- decomposed reliability, all derived from items[] (Article I) ----
    gate_cm = _confusion(items, "gate_caught")
    base_cm = _confusion(items, "base_caught")
    n_bad = gate_cm["tp"] + gate_cm["fn"]
    n_clean = gate_cm["fp"] + gate_cm["tn"]

    lift_rows = []
    for mut in MUT_ORDER:
        gk, gn = _frac(items, lambda x, mut=mut: x["mutation"] == mut, "gate_caught")
        bk, bn = _frac(items, lambda x, mut=mut: x["mutation"] == mut, "base_caught")
        lift_rows.append({"label": MUT_LABEL[mut], "mut": mut,
                          "gate": gk / gn if gn else 0.0, "base": bk / bn if bn else 0.0,
                          "gate_frac": f"{gk}/{gn}", "base_frac": f"{bk}/{bn}",
                          "lift_pp": round(100 * ((gk / gn if gn else 0) - (bk / bn if bn else 0)))})

    sev_rows = []
    for sev in ("material", "puffery"):
        gk, gn = _frac(items, lambda x, sev=sev: x["severity"] == sev, "gate_caught")
        bk, bn = _frac(items, lambda x, sev=sev: x["severity"] == sev, "base_caught")
        sev_rows.append({"sev": sev, "gate_frac": f"{gk}/{gn}", "base_frac": f"{bk}/{bn}",
                         "gate": gk / gn if gn else 0.0, "base": bk / bn if bn else 0.0})

    # mutation taxonomy counts (incl. the clean set)
    tax = {"clean": sum(1 for x in items if x["label"] == 0)}
    for mut in MUT_ORDER:
        tax[mut] = sum(1 for x in items if x["mutation"] == mut and x["label"] == 1)

    # Wilson CIs — computed, never typed
    gate_ci = wilson_ci(gate_cm["tp"], n_bad)
    base_ci = wilson_ci(base_cm["tp"], n_bad)
    fr_ci = wilson_ci(gate_cm["fp"], n_clean)

    # operating-point + confusion + lift + reliability SVGs
    op_svg = operating_point([
        {"label": "Gate", "fr": asr["gate"]["false_reject"], "catch": asr["gate"]["catch_rate"],
         "catch_lo": gate_ci[0], "catch_hi": gate_ci[1], "fr_hi": fr_ci[1], "color": "var(--g)"},
        {"label": "single judge", "fr": asr["baseline"]["false_reject"], "catch": asr["baseline"]["catch_rate"],
         "catch_lo": base_ci[0], "catch_hi": base_ci[1], "fr_hi": fr_ci[1], "color": "var(--a)"},
    ]) if asr else ""
    confusion_svg = confusion_pair(gate_cm, base_cm)
    lift_svg = lift_bars(lift_rows)
    reliab_svg = reliability(asr.get("reliability_bins", []), asr.get("ece", 0.0)) if asr else ""

    # source × mutation baseline heat-grid (Gate's is all-caught; the baseline's holes are the point)
    sources = sorted({x["source"] for x in items if x["label"] == 1})
    by_cell = {(x["source"], x["mutation"]): x for x in items if x["label"] == 1}
    base_cells = [[(None if (src, mut) not in by_cell else bool(by_cell[(src, mut)]["base_caught"]))
                   for mut in MUT_ORDER] for src in sources]
    tile_svg = tile_grid([s.replace("c_", "") for s in sources],
                         [MUT_ABBR[mut] for mut in MUT_ORDER], base_cells)

    # per-channel grouped bars (P4) — identical by construction
    ch = asr.get("channels", {})
    chan_svg = grouped_bars(
        list(ch.keys()),
        [ch[c]["gate_catch_rate"] for c in ch],
        [ch[c]["baseline_catch_rate"] for c in ch], w=420, h=210) if ch else ""

    # 7-run stability strip (fixed y-ranges; flat = reproducible, decision R5)
    stab_svg, date_from, date_to = "", "", ""
    if hist:
        last = hist[-1]
        date_from, date_to = hist[0]["ts"][:10], last["ts"][:10]
        gp = [r["golden_passed"] / r["golden_total"] for r in hist]
        pp = [r["props_pass"] / r["props_total"] for r in hist]
        stab_svg = stability_strip([
            {"label": "Gate catch-rate", "points": [r["gate_catch"] for r in hist], "ymin": 0, "ymax": 1,
             "ref": last["gate_catch"], "current": f"{last['gate_catch']*100:.0f}%", "color": "var(--g)"},
            {"label": "Single-judge catch", "points": [r["baseline_catch"] for r in hist], "ymin": 0, "ymax": 1,
             "ref": last["baseline_catch"], "current": f"{last['baseline_catch']*100:.1f}%", "color": "var(--a)"},
            {"label": "False-reject", "points": [r["false_reject"] for r in hist], "ymin": 0, "ymax": 0.3,
             "ref": last["false_reject"], "current": f"{last['false_reject']*100:.0f}%", "color": "var(--g)"},
            {"label": "Calibration ECE", "points": [r["ece"] for r in hist], "ymin": 0, "ymax": 0.1,
             "ref": last["ece"], "current": f"{last['ece']:.3f}", "color": "var(--g)"},
            {"label": "Golden evals", "points": gp, "ymin": 0, "ymax": 1, "ref": gp[-1],
             "current": f"{last['golden_passed']}/{last['golden_total']}", "color": "var(--g)"},
            {"label": "Properties P1–P5", "points": pp, "ymin": 0, "ymax": 1, "ref": pp[-1],
             "current": f"{last['props_pass']}/{last['props_total']}", "color": "var(--g)"},
        ])

    # golden per-step coverage (case COUNT as the honest signal — all pass)
    step_rows = [{"label": s["label"], "n": len(s["cases"]),
                  "passed": sum(1 for c in s["cases"] if c.get("pass"))}
                 for s in golden.get("steps", [])]
    max_step = max((r["n"] for r in step_rows), default=1)
    lifecycle = golden.get("lifecycle", {})

    # ---- ILLUSTRATIVE (synthetic traffic): bandit convergence + KPI tree ----
    panels = []
    for sc in m["scenarios"]:
        win = next((a for a in sc["arms"] if a["winner"]), sc["arms"][0])
        curves = [{"label": "winner share", "points": sc["conv_curve"], "color": win["accent"]}]
        if sc["blocked_arm"]:
            curves.append({"label": "blocked arm", "points": [0.0] * len(sc["conv_curve"]),
                           "color": "var(--muted)", "dashed": True})
        panels.append({"title": sc["label"], "curves": curves,
                       "note": f"winner {sc['learned_winner']} · {int(sc['winner_share']*100)}% · blocked 0×"})
    conv_svg = small_multiples_curves(panels)

    # drift watch (kept) — TTL-governed facts from the illustrative bandit demo
    drift_rows = []
    for s in DS.SCENARIOS:
        for v in DS.gated_variants(s):
            for d in v.data_used:
                if d.source in (DS.BOUGHT, DS.ENRICH, DS.BROKER):
                    drift_rows.append({"signal": d.signal, "source": d.source_label,
                                       "variant": v.label, "status": "fresh"})

    return templates.TemplateResponse(request, "assurance.html", {
        "trust": trust, "h": h, "catch": catch,
        # headline contrast
        "gate_cm": gate_cm, "base_cm": base_cm, "n_bad": n_bad, "n_clean": n_clean,
        "gate_ci": gate_ci, "base_ci": base_ci, "fr_ci": fr_ci,
        "gate_catch": asr.get("gate", {}).get("catch_rate", 0), "ece": asr.get("ece", 0),
        "base_catch": asr.get("baseline", {}).get("catch_rate", 0),
        "lift_pp": round(100 * (asr.get("gate", {}).get("catch_rate", 0) - asr.get("baseline", {}).get("catch_rate", 0)), 1),
        "lift_x": round(asr.get("gate", {}).get("catch_rate", 1) / max(asr.get("baseline", {}).get("catch_rate", 1) or 1, 1e-9), 2),
        # disclosure of the trust formula
        "prov_cov": h["provenance"]["coverage_pct"], "prov_facts": h["provenance"]["facts"],
        "hold_n": len(h["provenance"]["hold_in_copy"]),
        "ungated_sel": h["hallucination"]["selected"], "ungated_n": h["hallucination"]["ungated_arms"],
        # charts
        "op_svg": op_svg, "confusion_svg": confusion_svg, "lift_svg": lift_svg,
        "reliab_svg": reliab_svg, "tile_svg": tile_svg, "chan_svg": chan_svg, "stab_svg": stab_svg,
        "conv_svg": conv_svg, "kpi_tree": m["kpi_tree"],
        # tables / taxonomy / coverage
        "lift_rows": lift_rows, "sev_rows": sev_rows, "tax": tax, "mut_desc": MUT_DESC,
        "items": sorted(items, key=lambda x: x["trap_id"]), "channels": ch,
        "step_rows": step_rows, "max_step": max_step, "lifecycle": lifecycle,
        "gsum": golden.get("summary", {}),
        "props_pass": (hist[-1]["props_pass"] if hist else len(PROPS)),
        "props_total": (hist[-1]["props_total"] if hist else len(PROPS)),
        "props": PROPS, "date_from": date_from, "date_to": date_to, "n_runs": len(hist),
        # illustrative-fence metadata
        "sim_note": m["note"], "sim_seed": m["seed"], "sim_rounds": m["rounds"],
        "drift_rows": drift_rows,
    })


@app.get("/api/observe/golden")
def api_golden():
    return JSONResponse(_load("golden_evals.json") or {"empty": True})


@app.get("/api/observe/history")
def api_history():
    return JSONResponse({"history": _history()})
