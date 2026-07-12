W5/T-10 ship protocol (orchestrator-run, after T-08+T-09 merged):
1. bash .rapid/p6-exit-check.sh — must write .rapid/P6_EXIT.json with pass:true (all tasks done, full gate, WF-DESIGN 30/30 active, no legacy chrome, secret scan). Red = fix via gap loop, never force.
2. Manifest cap check: PYTHONPATH=. .venv/bin/python -m scripts.warm_hero_cache --check (T-06's mode) — caps hold.
3. Deploy: railway up --ci retry loop ≤8 (61MB upload flaky). 4. Prod sweep: the deployment-review loop's route+marker checks vs johnnycchung.com incl. /skyfiapt 200 + designer sd-* markers live + S02 realtime beat reachable.
5. git push origin deploy/railway. 6. Write .rapid/RETRO.md from the template; update docs/audits/DEPLOY-VS-SPEC.md ledger (gaps→resolved).
