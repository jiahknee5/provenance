"""Optimizer Assurance Lab — the growth / A/B surface of the platform.

  GET /optimizer — business-facing dashboard: every proposed A/B test across both
                   tenants, adversarially fact-checked, ranked by *realistic* KPI lift,
                   and wired to the truth-bounded bandit. The same assurance discipline
                   that proves the Gate, applied to the optimizer's own copy proposals.

Static research output (swarm run wf_232c4b39-b48); see docs/AB-TEST-OPPORTUNITIES.md.
"""
from __future__ import annotations

import random

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.context import ctx
from app.server import app, templates
from pipeline.personalization import demo_sim


@app.get("/optimizer", response_class=HTMLResponse)
def optimizer(request: Request):
    m = demo_sim.build()
    return templates.TemplateResponse(request, "optimizer.html", {
        "scenarios": m["scenarios"], "note": m["note"]})


@app.get("/optimizer/bandit-dashboard", response_class=HTMLResponse)
def optimizer_bandit_dashboard(request: Request):
    return templates.TemplateResponse(request, "bandit_dashboard.html", {})


@app.get("/optimizer/bandit-dashboard/learn-more", response_class=HTMLResponse)
def optimizer_bandit_learn_more(request: Request):
    return templates.TemplateResponse(request, "bandit_dashboard_learn_more.html", {})


@app.post("/api/optimizer/demo/fast-forward")
async def optimizer_demo_fast_forward(request: Request) -> JSONResponse:
    """Execute exactly 1,000 demo Thompson-sampling transitions on the backend."""
    payload = await request.json()
    posteriors = payload.get("posteriors", {})
    arms_by_prefix = payload.get("arms", {})
    segment_ids = [s for s in payload.get("segment_ids", []) if s in posteriors]
    gate_active = bool(payload.get("gate_active", True))
    stats = payload.get("global_stats", {})
    rng = random.Random(payload.get("seed"))

    for key in ("sends", "clicks", "unsubs", "blockedLies", "exploitCount",
                "exploreCount", "cumulativeRegret"):
        stats.setdefault(key, 0)
    eligible_segment_ids = []
    for segment_id in segment_ids:
        prefix = segment_id.split("__", 1)[0]
        if any(
            not (gate_active and arm.get("id") == "LIE")
            and posteriors[segment_id].get(arm.get("id"), {}).get("status") != "archived"
            for arm in arms_by_prefix.get(prefix, [])
        ):
            eligible_segment_ids.append(segment_id)
    if not eligible_segment_ids:
        return JSONResponse({"error": "No valid demo segments supplied."}, status_code=400)

    recent_events: list[dict] = []
    for _ in range(1000):
        segment_id = rng.choice(eligible_segment_ids)
        prefix = segment_id.split("__", 1)[0]
        all_arms = arms_by_prefix.get(prefix, [])
        valid_arms = [
            arm for arm in all_arms
            if not (gate_active and arm.get("id") == "LIE")
            and posteriors[segment_id].get(arm.get("id"), {}).get("status") != "archived"
        ]
        if gate_active and rng.random() < 0.28:
            stats["blockedLies"] += 1

        def mean(arm: dict) -> float:
            state = posteriors[segment_id][arm["id"]]
            return state["alpha"] / (state["alpha"] + state["beta"])

        leader_id = max(valid_arms, key=mean)["id"]
        samples = {
            arm["id"]: rng.betavariate(
                posteriors[segment_id][arm["id"]]["alpha"],
                posteriors[segment_id][arm["id"]]["beta"],
            )
            for arm in valid_arms
        }
        chosen = max(valid_arms, key=lambda arm: samples[arm["id"]])
        chosen_id = chosen["id"]
        state = posteriors[segment_id][chosen_id]
        is_exploiting = chosen_id == leader_id
        stats["exploitCount" if is_exploiting else "exploreCount"] += 1
        best_truth = max(float(arm.get("latentCTR", 0)) for arm in valid_arms)
        stats["cumulativeRegret"] += max(0, best_truth - float(chosen.get("latentCTR", 0)))

        roll = rng.random()
        unsub_rate = float(chosen.get("unsubRate", 0))
        ctr = float(chosen.get("latentCTR", 0))
        outcome = "unsub" if roll < unsub_rate else "click" if roll < unsub_rate + ctr else "no-click"
        stats["sends"] += 1
        state["sends"] += 1
        if outcome == "click":
            stats["clicks"] += 1
            state["clicks"] += 1
            state["alpha"] += 1
        elif outcome == "unsub":
            stats["unsubs"] += 1
            state["unsubs"] += 1
            state["beta"] += 3
        else:
            state["beta"] += 1

        recent_events.append({
            "segment_id": segment_id,
            "arm_id": chosen_id,
            "outcome": outcome,
            "is_exploiting": is_exploiting,
            "sample": samples[chosen_id],
        })
        if len(recent_events) > 50:
            recent_events.pop(0)

    return JSONResponse({
        "sends_processed": 1000,
        "posteriors": posteriors,
        "global_stats": stats,
        "recent_events": recent_events,
    })


@app.get("/api/optimizer/live")
def optimizer_live() -> JSONResponse:
    """Live posteriors moving from REAL /site traffic — the online counterpart to the
    simulated campaign above. Settles overdue impressions first so no-clicks count."""
    c = ctx()
    c.live.settle()
    return JSONResponse(c.live.snapshot())


@app.get("/api/optimizer/dashboard")
def optimizer_dashboard() -> JSONResponse:
    """Dashboard-shaped view of the real online optimizer.

    The HTML dashboard has a separate demo trigger, but its default mode should observe the
    same live optimizer that serves /site traffic instead of running a second client-only
    simulation.
    """
    c = ctx()
    settled = c.live.settle()
    return JSONResponse({
        "mode": "live",
        "settled": settled,
        "snapshot": c.live.snapshot(),
        "lift": c.live.lift_report(),
    })


@app.post("/api/optimizer/live/settle")
def optimizer_live_settle() -> JSONResponse:
    """Resolve impressions with no click as reward-0 (the bandit's negative evidence)."""
    return JSONResponse({"settled": ctx().live.settle()})


@app.get("/api/optimizer/lift")
def optimizer_lift() -> JSONResponse:
    """Measured lift: CTR of the adaptive (bandit) slice vs the random (control) holdout.
    This is the bandit proving it beats random serving on REAL traffic, not just asserting it."""
    c = ctx()
    c.live.settle()
    return JSONResponse(c.live.lift_report())
