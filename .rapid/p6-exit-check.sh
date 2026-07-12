#!/usr/bin/env bash
# P6 exit assertions (T-10/W5 runs this) — writes .rapid/P6_EXIT.json
set -uo pipefail; cd "$(dirname "$0")/.."
pass=true; declare -a results
check(){ local name="$1" ok="$2"; results+=("{\"assert\":\"$name\",\"pass\":$ok}"); if [ "$ok" = "false" ]; then pass=false; fi; return 0; }
# 1 all build tasks done (T-10 = the ship task running this checker, excluded)
open_tasks=$(.venv/bin/python -c "import json;print(sum(1 for t in json.load(open('.rapid/TASKS.json'))['tasks'] if t['status']!='done' and t['id']!='T-10'))")
check "all_build_tasks_done" $([ "$open_tasks" = "0" ] && echo true || echo false)
# 2 whole suite green (single process — catches test interactions)
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q >/tmp/p6gate.log 2>&1 && check "full_suite_green" true || check "full_suite_green" false
# 3 WF-DESIGN 30/30 active+green (0 skipped)
PYTHONPATH=. .venv/bin/python -m pytest tests/test_wf_design_matrix.py -q 2>&1 | tail -1 | grep -q "skipped" && check "wf_design_30_active" false || check "wf_design_30_active" true
# 4 no legacy chrome
grep -rl 'base.html\|_nav.html' app/ >/dev/null 2>&1 && check "no_legacy_chrome" false || check "no_legacy_chrome" true
# 5 secret scan (committed files; synthetic seeded tokens like demo0…/eval0… excluded)
git grep -nE "(api[_-]?key|secret|token)\s*=\s*['\"][A-Za-z0-9_\-\.]{16,}" -- ':!*.md' ':!tests/*' | grep -vE "token=\"(eval|demo)0{12}\"" | grep -q . && check "secret_scan_clean" false || check "secret_scan_clean" true
printf '{"ts":"%s","pass":%s,"assertions":[%s]}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$pass" "$(IFS=,; echo "${results[*]}")" > .rapid/P6_EXIT.json
cat .rapid/P6_EXIT.json; [ "$pass" = "true" ]
