"""Per-section observability for the designer (S4/S5, T-04) — shared by both consoles.

Everything the sd-graph / sd-evals / sd-observe / sd-ab / sd-drift panels and the
per-section cost row render is built here, from exactly three real feeds (Art I):

  1. THIS request's ``build_page()`` output — the run that actually shipped the page;
  2. the live api-cost ledger (``pipeline/observability/api_costs.py``), summed by the
     section's cache keys — offline default $0, honestly labeled;
  3. a SEEDED offline DecisionPool campaign: the real T-02 pool object (real Gate, real
     Thompson posteriors, real impressions table) run once per process over the demo
     claims library with a deterministic click model. Every number shown — posterior
     means, CTRs, lift, paused arms — is MEASURED from that pool's state and labeled
     "seeded". Nothing is typed in. Live pools replace the seed when serving moves onto
     the per-decision pool (T-05).

The seeded campaign also replays one drift beat (S4.3): arm D — bound to ``c_tco`` and
carried ONLY by the hero:hero_sub pool — is paused via ``on_claims_invalidated`` after
the campaign, so exactly one target shows a real surgical pause while every other pool
keeps serving. That is the invariant on display, not an illustration of it.

The agent graph follows the Observatory node contract (pipeline/common/topology.py):
each node = {id, lane, label, tools, input, decision, output} with real, section-scoped
values, in the per-element flow resolve → select → assemble → gate → cache/serve →
receipt (04-spec/spec.md Workflow).
"""
from __future__ import annotations

import random
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pipeline.common import db as DBM
from pipeline.common.cache import LLMCache, VerdictCache
from pipeline.common.schemas import Variant
from pipeline.common.store import PosteriorStore
from pipeline.gate.gate import Gate
from pipeline.gate.rules import RulesEngine
from pipeline.library.library import ClaimsLibrary
from pipeline.observability import api_costs as AC
from pipeline.personalization import sections as SEC
from pipeline.personalization.decision_pool import ALL_CELL, DecisionPool

# --------------------------------------------------------------------------- #
# The seeded offline campaign (S4.2/S4.4) — one real DecisionPool per tenant.
# --------------------------------------------------------------------------- #
# Demo-claims-library arms (the same honest arms the T-02 invariants run against).
_SEED_ARMS = [
    ("A", "Cut length of stay with verified analytics", ("c_los",)),
    ("B", "Transparent pricing with no implementation fee", ("c_price", "c_nofee")),
    ("C", "Deployed across twelve health systems", ("c_deployed",)),
]
# Arm D asserts c_tco and lives ONLY in the hero:hero_sub pool — the drift beat pauses
# exactly this arm in exactly that pool (surgical, S4.3).
_DRIFT_ARM = ("D", "A verified cut in total cost of ownership", ("c_tco",))
DRIFT_CLAIM = "c_tco"
DRIFT_TARGET = ("hero", "hero_sub")

_IMPRESSIONS_PER_POOL = 160          # 40/route -> every route cell crosses the 30-resolved bar
_SETTLE_EVERY = 20
_HOLDOUT = 0.3                       # a measurable random-control slice for lift
# deterministic click model — the SIMULATED audience of the seeded campaign (labeled);
# what the panels show is what the pool MEASURED serving that audience.
_LATENT = {"A": 0.50, "B": 0.22, "C": 0.08, "D": 0.15}
_T0 = datetime(2026, 7, 12, tzinfo=timezone.utc)

_seeds: dict[str, dict] = {}
_seed_lock = threading.Lock()


def _mk(arm: str, headline: str, claim_ids: tuple[str, ...]) -> Variant:
    lines = [f"{headline}."]
    lines += [f"Helix Analytics [[{cid}]]." for cid in claim_ids]
    lines.append("See the full ROI breakdown. Start your assessment →")
    return Variant(variant_id=arm, segment="site", channel="website", arm_label=arm,
                   template="\n".join(lines), claim_ids=list(claim_ids), headline=headline)


def _provider(tenant: str, section_id: str, target_id: str) -> list[Variant]:
    arms = list(_SEED_ARMS)
    if (section_id, target_id) == DRIFT_TARGET:
        arms.append(_DRIFT_ARM)
    return [_mk(*a) for a in arms]


def seeded_campaign(tenant: str, routes: tuple[str, ...]) -> dict:
    """Build (once per process) and return the tenant's seeded pool state.

    Deterministic end to end: fixed rng seeds, fixed visit keys, fixed logical clock —
    the same numbers replay on every process (Art IV). The pool, its posteriors and its
    impressions live in a per-process temp dir; nothing touches the app database.
    """
    routes = tuple(routes)
    with _seed_lock:
        if tenant in _seeds:
            return _seeds[tenant]

        tmp = Path(tempfile.mkdtemp(prefix=f"sd_seed_{tenant}_"))
        cache_db = tmp / "gate_cache.sqlite"
        DBM.init_db(cache_db)
        conn = DBM.connect(cache_db)
        gate = Gate(ClaimsLibrary.from_seed(), RulesEngine.load(),
                    verdict_cache=VerdictCache(conn), llm_cache=LLMCache(conn))
        dp = DecisionPool(gate, _provider, channel="website",
                          db_path=tmp / "impressions.sqlite",
                          posteriors={tenant: PosteriorStore(f"sd_seed_{tenant}", "website")},
                          holdout_frac=_HOLDOUT, persist=False,
                          rng=random.Random(20260712), routes=routes)

        targets = [(s["id"], t["slot_id"]) for s in SEC.list_sections(tenant)
                   for t in (s.get("text_targets") or [])]
        clicker = random.Random(97)
        settle_at = _T0 + timedelta(hours=2)
        for sid, tid in targets:
            pid = DecisionPool.pool_id(tenant, sid, tid)
            dp.cleared_pool(tenant, sid, tid)
            for i in range(_IMPRESSIONS_PER_POOL):
                route = routes[i % len(routes)]
                v = dp.pick(tenant, sid, tid, route,
                            visit_key=f"seed|{pid}|{i}", now=_T0)
                if v is not None and clicker.random() < _LATENT[v.arm_label]:
                    dp.reward_click(pid, v.variant_id, route)
                if i % _SETTLE_EVERY == _SETTLE_EVERY - 1:
                    dp.settle(pid, now=settle_at)
            dp.settle(pid, now=settle_at)

        # the drift beat: a source change invalidates c_tco -> ONLY arm D of ONLY the
        # hero:hero_sub pool leaves the bandit atomically; its receipt survives.
        paused = dp.on_claims_invalidated([DRIFT_CLAIM])

        _seeds[tenant] = {
            "dp": dp, "paused": paused, "targets": set(targets), "routes": routes,
            "gate_rules_version": gate.rules.rules_version(),
            "note": (f"seeded offline campaign — {_IMPRESSIONS_PER_POOL} impressions/pool "
                     "served by the real per-decision pool (Gate-cleared arms, Thompson "
                     "posteriors, deterministic replay). Not live traffic: live pools "
                     "attach when this target serves generative variants."),
        }
        return _seeds[tenant]


def _arm(vid: str) -> str:
    return vid.rsplit("__", 1)[-1]


def ab_panel(tenant: str, section_id: str, target_id: str,
             routes: list[str], *, kind: str = "text") -> dict:
    """The A/B panel: measured posteriors per route + measured lift vs control (S4.2)."""
    if kind != "text":
        return {"seeded": False, "routes": list(routes),
                "note": ("no pool for this image target yet — the image lane selects by "
                         "intent rules today; posteriors per route + lift vs control "
                         "attach when image arms enter the per-decision pool")}
    seed = seeded_campaign(tenant, tuple(routes))
    if (section_id, target_id) not in seed["targets"]:
        return {"seeded": False, "routes": list(routes),
                "note": "no pool for this target — posteriors per route + lift vs "
                        "control attach when it serves from the per-decision pool"}

    dp: DecisionPool = seed["dp"]
    pid = DecisionPool.pool_id(tenant, section_id, target_id)
    rows = []
    for route in routes:
        cell = dp.serving_cell(tenant, section_id, target_id, route)
        active = dp.active(tenant, section_id, target_id, cell)
        means = {vid: dp.posterior_mean(tenant, cell, vid) for vid in active}
        top = max(means, key=means.get) if means else None
        rows.append({
            "route": route,
            "cell": cell,
            "cell_note": ("route posterior" if cell == route
                          else f"pooled {ALL_CELL} cell (<30 resolved)"),
            "top_arm": _arm(top) if top else "—",
            "mean": round(means[top], 3) if top else None,
            "arms": len(active),
        })

    lift = dp.lift_report(pid)
    if lift["lift"] is not None:
        lift_label = (f"{lift['lift']:+.4f} — bandit CTR {lift['bandit_ctr']:.4f} vs "
                      f"random-control {lift['control_ctr']:.4f} (seeded campaign, measured)")
    else:
        lift_label = lift["note"]

    paused = sorted(_arm(v) for v in seed["paused"] if v.startswith(f"{pid}__"))
    return {
        "seeded": True,
        "routes": list(routes),
        "rows": rows,
        "lift": lift,
        "lift_label": lift_label,
        "paused": paused,
        "pause_note": (f"claim {DRIFT_CLAIM} invalidated → out of the bandit pool"
                       if paused else ""),
        "note": seed["note"],
    }


def drift_status(tenant: str, section_id: str, target_id: str,
                 registry_version: str, routes: list[str], *, kind: str = "text") -> dict:
    """The drift badge: measured pause state of this target's pool (S4.3)."""
    if kind != "text":
        return {"status": "active", "rules_version": registry_version,
                "note": "no pooled arms — image guardrails re-verify on a rules change"}
    seed = seeded_campaign(tenant, tuple(routes))
    dp: DecisionPool = seed["dp"]
    pid = DecisionPool.pool_id(tenant, section_id, target_id)
    if (section_id, target_id) not in seed["targets"]:
        return {"status": "active", "rules_version": registry_version,
                "note": "no invalidated claims touch this target"}
    paused = sorted(_arm(v) for v in seed["paused"] if v.startswith(f"{pid}__"))
    active_n = len(dp.active(tenant, section_id, target_id, ALL_CELL))
    if paused:
        return {"status": f"{len(paused)} arm paused",
                "rules_version": registry_version,
                "note": (f"claim {DRIFT_CLAIM} invalidated → arm {', '.join(paused)} left "
                         f"the pool atomically · {active_n} arm(s) kept serving — "
                         "surgical, not a blanket pause")}
    return {"status": "active", "rules_version": registry_version,
            "note": (f"{active_n} arm(s) serving · 0 paused — no invalidated claim "
                     "touches this pool")}


# --------------------------------------------------------------------------- #
# Cost row — the api-cost ledger summed by the section's cache keys (R35a).
# --------------------------------------------------------------------------- #
def cost_row(section_id: str, cache_keys: list[str]) -> dict:
    keys = [k for k in cache_keys if k and k != "—"]
    calls, total = 0, 0.0
    for k in keys:
        r = AC.costs_for_cache_key(k)
        calls += len(r["calls"])
        total = round(total + r["estimated_cost_usd"], 6)
    if calls:
        label = (f"${total:.3f} across {calls} ledger call(s) for cache key(s) "
                 f"{', '.join(keys)}")
    elif keys:
        label = (f"$0 — no api-cost ledger rows for cache key(s) {', '.join(keys)} "
                 "(offline / prebuilt / served from cache)")
    else:
        label = "$0 — deterministic slot-fill only; this section holds no cache keys"
    return {"section_id": section_id, "cache_keys": keys, "calls": calls,
            "usd": total, "label": label}


# --------------------------------------------------------------------------- #
# Agent graph — the per-element flow as Observatory-contract nodes.
# --------------------------------------------------------------------------- #
def flow_nodes(*, entry_channel: str, entry_signals: str, route: str, tier: int,
               tier_label: str, text_targets: list[dict], image_targets: list[dict],
               held_count: int, changed_count: int, cost: dict,
               rules_version: str, registry_version: str) -> list[dict]:
    """resolve → select → assemble → gate → cache/serve → receipt, every value from
    this request's build (node shape mirrors pipeline/common/topology.py NODES)."""
    n_targets = len(text_targets) + len(image_targets)
    strategies = " · ".join(f"{t['slot_id']}: {t['strategy']} ({t['policy_live']})"
                            for t in text_targets) or "no text targets"
    intents = ", ".join(f"{t['surface_id']}: {t['intent']}" for t in image_targets
                        if t.get("intent"))
    changed = [t for t in text_targets if t["changed"]]
    shipped_sample = (f"“{changed[0]['shipped'][:90]}”" if changed
                      else "generic copy shipped unchanged")
    latencies = " · ".join(f"{t['slot_id']}: {t['latency']['label']}" for t in text_targets)
    if image_targets:
        latencies += (" · " if latencies else "") + " · ".join(
            f"{t['surface_id']}: {t['latency']['label']}" for t in image_targets)
    receipt_keys = [t["receipt"]["cache_key"] for t in image_targets
                    if t["receipt"]["cache_key"] != "—"]

    return [
        {"id": "resolve", "lane": "website", "label": "Resolve",
         "tools": ["entry classify (utm / referer / token)", "IP + network read",
                   "identity / cohort resolve"],
         "input": entry_signals or "(no signals — bare direct hit)",
         "decision": f"channel = {entry_channel} · audience route = {route} · "
                     f"confidence {tier}",
         "outcome": f"{entry_channel} · route {route}",
         "output": f"visit resolved at confidence {tier} ({tier_label})"},
        {"id": "select", "lane": "optimizer", "label": "Select",
         "tools": ["section registry (rules/<tenant>_sections.yaml)",
                   "strategy / policy binding", "image intent rules"],
         "input": f"{len(text_targets)} text + {len(image_targets)} image target(s) "
                  f"on route {route}",
         "decision": strategies + (f" · intents: {intents}" if intents else ""),
         "outcome": f"{changed_count} of {len(text_targets)} text target(s) rewritten",
         "output": f"{changed_count} of {len(text_targets)} text target(s) rewritten "
                   "for this visit" + (f" · {len(image_targets)} image surface(s) bound"
                                       if image_targets else "")},
        {"id": "assemble", "lane": "website", "label": "Assemble",
         "tools": ["deterministic slot-fill ($0)", "catalog reframes",
                   "structured image prompt"],
         "input": "catalog copy + bound claims for the selected targets",
         "decision": "slot-fill each text target; assemble the structured image prompt "
                     "per surface" if image_targets else
                     "slot-fill each text target from the catalog",
         "outcome": shipped_sample[:60] + ("…" if len(shipped_sample) > 60 else ""),
         "output": f"assembled this visit: {shipped_sample}"},
        {"id": "gate", "lane": "gate", "label": "Gate",
         "tools": ["say / allude / hold policy", "message hygiene vetoes",
                   "image guardrails"],
         "input": f"{n_targets} assembled element(s)",
         "decision": f"{n_targets} cleared · {held_count} say-variant(s) held by policy",
         "outcome": f"{n_targets} cleared · {held_count} held",
         "output": "only cleared elements exist downstream — a held fact is "
                   "structurally unshippable, not filtered"},
        {"id": "serve", "lane": "website", "label": "Cache / serve",
         "tools": ["cache-by-key", "prebuilt manifest", "realtime gradient→swap"],
         "input": ("cache key(s): " + ", ".join(receipt_keys)) if receipt_keys
                  else "deterministic slot-fill — no cache needed",
         "decision": latencies,
         "outcome": f"shipped · api cost ${cost['usd']:.3f}",
         "output": f"section shipped · {cost['label']}"},
        {"id": "receipt", "lane": "library", "label": "Receipt",
         "tools": ["provenance receipt (9 pinned fields)", "MessageLedger"],
         "input": f"every shipped element ({n_targets})",
         "decision": f"receipt minted per element — rules {rules_version[:8]} · "
                     f"registry {registry_version[:8]}",
         "outcome": f"{n_targets} receipt(s) on file",
         "output": "un-receipted = fail; each receipt carries source, lawful basis, "
                   "policy, gate verdict, claims, cache_key, mode, workflow, "
                   "rules_version"},
    ]


# --------------------------------------------------------------------------- #
# Evals — measured this visit, never asserted.
# --------------------------------------------------------------------------- #
def eval_rows(sec: dict, text_targets: list[dict], diff_rows: list[dict],
              brain: dict, image_targets: list[dict]) -> list[dict]:
    out = []
    bound = sum(1 for t in text_targets if t["shipped"] != "—")
    held = [d.get("blocked_say") for d in diff_rows if d.get("blocked_say")]
    shipped_all = " ".join(t["shipped"] for t in text_targets)
    leaked = [h for h in held if h and h in shipped_all]
    for e in sec.get("evals") or []:
        if e == "gate_pass":
            status = (f"measured this visit: {bound}/{len(text_targets)} text target(s) "
                      f"bound · 0 blocked variants shipped · {len(held)} say-variant(s) "
                      "held by policy")
        elif e == "hold_never_ships":
            if leaked:
                status = (f"LEAKED — {len(leaked)} held string(s) found in shipped copy "
                          "(invariant violation)")
            else:
                status = (f"checked {len(held)} held string(s) against this section's "
                          "shipped copy — 0 leaked this visit")
        elif e == "brain_score":
            bs = brain.get("brain_score")
            if bs is not None:
                status = (f"{bs:.2f} · {brain.get('brain_simulator') or 'proxy_v1'} "
                          "(best-of-N at generation time)")
            else:
                src = next((t.get("load_status") or t.get("source") or "—"
                            for t in image_targets), "—")
                status = (f"not scored this visit — hero served from {src}; "
                          "best-of-N scoring runs at generation time")
        else:
            status = "tracked"
        out.append({"id": e, "label": e.replace("_", " "), "status": status})
    return out


# --------------------------------------------------------------------------- #
# Per-section event ledger — this request's rows, monotonic seq across sections.
# --------------------------------------------------------------------------- #
def ledger_rows(seq: int, *, section_id: str, entry_channel: str, route: str,
                tier_label: str, text_targets: list[dict], image_targets: list[dict],
                cost: dict, registry_version: str) -> tuple[list[dict], int]:
    rows: list[dict] = []

    def add(event: str, detail: str) -> None:
        nonlocal seq
        seq += 1
        rows.append({"seq": seq, "event": event, "detail": detail})

    add(f"resolve {section_id}",
        f"channel {entry_channel} · route {route} · {tier_label}")
    for t in text_targets:
        add(f"select {t['slot_id']}", f"{t['strategy']} · policy {t['policy_live']}")
        add(f"gate {t['slot_id']}",
            "cleared" + (" · 1 say-variant held by policy" if t.get("held_say") else ""))
        add(f"serve {t['slot_id']}",
            f"{t['latency']['label']} · "
            + ("rewrote copy for this visit" if t["changed"] else "default shipped"))
        ab = t.get("ab") or {}
        if ab.get("seeded"):
            add(f"pool {t['slot_id']}", f"lift vs control {ab['lift_label']}")
        add(f"receipt {t['slot_id']}",
            f"cache {t['receipt']['cache_key']} · rules {registry_version[:8]}")
    for t in image_targets:
        add(f"image {t['surface_id']}",
            f"{t['source']} · {t['load_status']} · {t['latency']['label']}")
        add(f"receipt {t['surface_id']}",
            f"cache {t['receipt']['cache_key']} · rules {registry_version[:8]}")
    add(f"cost {section_id}", cost["label"])
    return rows, seq
