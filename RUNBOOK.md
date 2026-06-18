# RUNBOOK — Provenance demo

Everything runs **offline and deterministically** (no API key). Python 3.11 venv.

## Setup (once)
```bash
cd ~/projects/lyso/provenance
/Users/johnny/.local/bin/python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Run the eval harness (the 5 headline properties + E1 + per-module)
```bash
.venv/bin/python -m pytest -q
```
34 tests. They hit the real Gate + the Enrichment Gate (no mocks) and are seed-locked.

## Run the full demo pipeline (generates all artifacts, deterministically)
```bash
.venv/bin/python -m scripts.pipeline
```
Prints a summary and writes `data/demo/runs/*.json` (campaigns, twin, drift, assurance,
ledgers, learnings, demo_state, summary). Re-running is byte-identical.

## Run the Observatory trace (the watchable, per-node recorded run)
```bash
.venv/bin/python -m scripts.trace
```
Runs the full pipeline + the enrichment touchpoint with the observability recorder attached.
Writes the append-only event ledger `data/demo/observe/*.jsonl` (one per lane), the node
graph (`topology.json`), the per-node input/decision/output evals (`node_evals.json`), the
profile DB, and `meta.json` (P1–P5 + E1 verdicts). Byte-identical re-run in synthetic mode.

## Start the app (form + website + inspector + Observatory + enrichment catalog)
```bash
PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --port 8099
```
- `http://localhost:8099/` — the lead form → submit (enriches + gates a profile) → magic link → personalized page
- `http://localhost:8099/site/<token>` — the website: only Gate-passed claims + a "personalized, with receipts" panel (gated facts + their lawful basis)
- `http://localhost:8099/inspector` — the five-module inspector (run the pipeline first)
- `http://localhost:8099/observatory` — the live node graph + tooling + per-node I/O evals + timeline (run the trace first)
- `http://localhost:8099/enrichment-catalog` — every paid/free enrichment source + DB locations + the live gated profile

## Optional: live enrichment (one real, free connector)
Default enrichment is synthetic + offline + $0. To use the live news-RSS connector (cached,
$0, no PII to third parties — see `docs/audits/enrichment-privacy.md`):
```bash
PROVENANCE_ENRICH=live PYTHONPATH=. .venv/bin/python -m uvicorn app.main:app --port 8099
```

## Optional: the "rich" inference profile (real models)
The default is deterministic + offline. To upgrade the verifier with real models:
```bash
.venv/bin/python -m pip install -r requirements-optional.txt      # transformers/torch, anthropic
PROVENANCE_PROFILE=rich .venv/bin/python -m scripts.pipeline       # DeBERTa NLI + Ollama judges
# Claude judge also engages if ANTHROPIC_API_KEY is set in the env / a .env
```
First rich run downloads DeBERTa-v3-large-MNLI (~1.6GB, one-time). All model outputs are
cached, so a rich run replays deterministically afterward.

## The demo flow (what the inspector shows)
form → 1000 recipients → Claims Library + Gate → **Campaign 1** (bandit over verified arms,
simulated CTA; the lie is structurally unreachable) + the unconstrained twin (converges to
the lie) → **drift** (legal hold flips → ROI variant pauses) → **Campaign 2** (warm-started,
lower regret) → **website** (same Gate, A/B-winning verified variant, CTA) → **Assurance Lab**
(Gate vs single judge, per channel).

**Enrichment touchpoint** (data-provenance, see `docs/04-workflow/ENRICHMENT-TOUCHPOINTS.md`):
form → **enrich** (connectors fan out) → **Enrichment Gate** (allow-listed source + lawful
basis + freshness + consent → usable/disclaimer/blocked) → **synthesize** a profile DB →
**personalize** (only gated facts reach the copy, each with its receipt) → **fact audit**
(the Assurance Lab proves the gate blocks disallowed/stale/PHI/non-consent facts — property E1).
