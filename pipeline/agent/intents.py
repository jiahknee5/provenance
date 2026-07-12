"""The agent's intents — deterministic handlers over the engine state.

Each returns a uniform result dict the /agent surface renders:
  { title, summary, cards:[{k,v,sub,tone}], table:{cols,rows}|None,
    provenance:[{signal,source,policy}], note, followups:[{q,label}] }
Every cell in table.rows is {"v":str,"pill":cls|None}.
"""
from __future__ import annotations

from pipeline.personalization import cohort as C
from pipeline.personalization import demo_scenarios as DS
from pipeline.personalization import demo_sim


def _cell(v, pill=None):
    return {"v": str(v), "pill": pill}


# --------------------------------------------------------------------------- #
INTENTS = [
    {"id": "why_won", "q": "Why did a variant win?", "icon": "ph-trophy"},
    {"id": "kpis", "q": "How are my KPIs tracking?", "icon": "ph-trend-up"},
    {"id": "drift", "q": "Is anything drifting?", "icon": "ph-waves"},
    {"id": "assurance", "q": "Can I trust the personalization?", "icon": "ph-shield-check"},
    {"id": "records", "q": "Show me the hottest records", "icon": "ph-table"},
]
_FOLLOW = [{"q": i["q"], "label": i["q"]} for i in INTENTS]


def route(query: str) -> str:
    q = (query or "").lower()
    if any(w in q for w in ("win", "winner", "why", "best variant", "optimiz", "bandit")):
        return "why_won"
    if any(w in q for w in ("kpi", "metric", "target", "track", "lift", "conversion")):
        return "kpis"
    if any(w in q for w in ("drift", "stale", "expire", "fresh")):
        return "drift"
    if any(w in q for w in ("trust", "assur", "hallucin", "prove", "provenance", "overclaim")):
        return "assurance"
    if any(w in q for w in ("record", "hot", "lead", "pipeline", "deal", "contact")):
        return "records"
    return "why_won"


# --- handlers ---------------------------------------------------------------- #
def _why_won(m: dict) -> dict:
    sc = m["scenarios"][0]
    winner = next(a for a in sc["arms"] if a["id"] == sc["learned_winner"])
    blocked = sc["blocked_arm"]
    found = DS.find_variant(sc["id"], winner["id"])
    prov = [{"signal": d.signal, "source": d.source_label, "policy": d.policy}
            for d in (found[1].data_used if found else [])]
    rows = [[_cell(a["label"] + (" ★" if a["winner"] else "")),
             _cell(f"{int(a['share']*100)}%"), _cell(a["posterior_mean"]),
             _cell(a["kpi"], "b")] for a in sc["arms"]]
    if blocked:
        rows.append([_cell(blocked["label"]), _cell("0%"), _cell("—"), _cell("blocked", "r")])
    return {
        "title": "Why the winner won",
        "summary": f"In “{sc['label']}”, the optimizer learned **{winner['label']}** wins "
                   f"({int(sc['winner_share']*100)}% of traffic).",
        "cards": [
            {"k": "Learned winner", "v": winner["id"], "sub": winner["label"], "tone": "g"},
            {"k": "Posterior mean", "v": winner["posterior_mean"], "sub": "Beta estimate of CTR", "tone": ""},
            {"k": "Ungated arm picks", "v": blocked["selections"] if blocked else 0,
             "sub": "the creepy variant — provably never", "tone": "g"},
        ],
        "table": {"cols": ["Variant", "Traffic", "Posterior", "Optimizes"], "rows": rows},
        "provenance": prov,
        "note": (f"The ungated variant “{blocked['label']}” would win on raw CTR, but it relies on a "
                 "`hold` fact, so the Gate keeps it out of the action pool — the bandit can't pull it. "
                 "That's the proof you can't win by lying." if blocked else None),
        "followups": _FOLLOW,
    }


def _kpis(m: dict) -> dict:
    leaves = [k for g in m["kpi_tree"] for k in g["kpis"]]
    on = sum(1 for k in leaves if k["pct_to_target"] >= 60)
    cards = []
    for k in sorted(leaves, key=lambda x: -x["pct_to_target"])[:4]:
        tone = "g" if k["pct_to_target"] >= 60 else ("a" if k["pct_to_target"] >= 25 else "")
        cards.append({"k": k["label"], "v": f"{k['current']}{k['unit'] if k['unit']=='%' else ''}",
                      "sub": f"{int(k['pct_to_target'])}% to target", "tone": tone})
    rows = [[_cell(k["label"]), _cell(f"{k['baseline']}"), _cell(f"{k['current']}"),
             _cell(f"{k['target']}"), _cell(f"{int(k['pct_to_target'])}%",
             "g" if k["pct_to_target"] >= 60 else ("a" if k["pct_to_target"] >= 25 else None))]
            for k in leaves]
    return {
        "title": "KPI tracking (simulated)",
        "summary": f"Optimizing toward **{len(leaves)} master KPIs** — **{on}** on track to target.",
        "cards": cards,
        "table": {"cols": ["KPI", "Baseline", "Now", "Target", "Progress"], "rows": rows},
        "provenance": [],
        "note": "Simulated reinforcement-learning result — deterministic seeded bandit, no live traffic.",
        "followups": _FOLLOW,
    }


def _drift(m: dict) -> dict:
    d = m["health"]["drift"]
    return {
        "title": "Drift watch",
        "summary": (f"**{d['paused']} variants paused**. {d['fresh']}/{d['ttl_facts']} "
                    "TTL-governed facts are fresh."),
        "cards": [
            {"k": "Paused variants", "v": d["paused"], "sub": "from source change", "tone": "g" if d["paused"] == 0 else "a"},
            {"k": "Fresh facts", "v": f"{d['fresh']}/{d['ttl_facts']}", "sub": "bought/enrich, TTL-governed", "tone": ""},
        ],
        "table": None, "provenance": [],
        "note": d["note"] + ". On a source change Drift pauses the dependent arm automatically.",
        "followups": _FOLLOW,
    }


def _assurance(m: dict) -> dict:
    h = m["health"]
    catch = h["hallucination"]["trap_catch_rate"]
    return {
        "title": "Can you trust it?",
        "summary": (f"Provenance **{h['provenance']['coverage_pct']}%** across "
                    f"{h['provenance']['facts']} facts · **{h['hallucination']['selected']}** ungated "
                    "arms ever selected."),
        "cards": [
            {"k": "Provenance", "v": f"{h['provenance']['coverage_pct']}%", "sub": "facts with a source", "tone": "g"},
            {"k": "Hold-in-copy", "v": len(h["provenance"]["hold_in_copy"]), "sub": "never recited", "tone": "g"},
            {"k": "Ungated selected", "v": h["hallucination"]["selected"],
             "sub": f"of {h['hallucination']['ungated_arms']} blocked", "tone": "g"},
            {"k": "Trap catch-rate", "v": (f"{catch}%" if catch else "structural"),
             "sub": "Assurance Lab", "tone": "g"},
        ],
        "table": None, "provenance": [],
        "note": "Every shown fact carries a source; hold facts only steer, never appear in copy.",
        "followups": _FOLLOW,
    }


def _records(m: dict) -> dict:
    people = sorted(C.COHORT, key=lambda p: -p["hubspot"]["lead_score"])[:6]
    _pill = {"customer": ("g", "Customer"), "sql": ("b", "SQL"), "mql": ("a", "MQL"),
             "lead": ("v", "Lead"), "visitor": (None, "Visitor")}
    rows = []
    for p in people:
        v = C.view(p)
        cls, lbl = _pill.get(v["hubspot"]["lifecycle"], (None, v["hubspot"]["lifecycle"]))
        rows.append([_cell(v["name"]), _cell(v["linkedin"]["company"] or "—"),
                     _cell(lbl, cls), _cell(v["hubspot"]["lead_score"])])
    return {
        "title": "Hottest records",
        "summary": f"Top **{len(rows)}** records by lead score.",
        "cards": [], "table": {"cols": ["Record", "Company", "Stage", "Score"], "rows": rows},
        "provenance": [], "note": "Source: HubSpot lifecycle + lead score (first-party).",
        "followups": _FOLLOW,
    }


_HANDLERS = {"why_won": _why_won, "kpis": _kpis, "drift": _drift,
             "assurance": _assurance, "records": _records}


def run(query: str) -> dict:
    intent = route(query)
    m = demo_sim.build()
    res = _HANDLERS[intent](m)
    res["intent"] = intent
    res["query"] = query
    return res
