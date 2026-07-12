# W1 supervisor common rules (all four)
Repo /Users/johnny/projects/provenance. Structure: orchestrator→YOU→implementors/testers.
- You run in YOUR OWN git worktree/branch (spawned with worktree isolation). Commit your work ON YOUR BRANCH only, message "T-0X: <what> (SY/Rn)" + Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>. NEVER push, NEVER deploy, NEVER touch .rapid/TASKS.json or .rapid/MEMORY.md (the orchestrator merges + updates state).
- Art VII: tests/test_wf_design_matrix.py and the 5 property tests are LOCKED — never edit. Add NEW test files only.
- Verify by RUNNING (pytest exact commands in your brief); commit only on all-green incl. the full deploy gate:
  PYTHONPATH=. .venv/bin/python -m pytest tests/test_api_costs.py tests/test_brain_simulator.py tests/test_gauntlet_site.py tests/test_hero_image.py tests/test_planet_site.py tests/test_planet_hero_image.py tests/test_planet_motion.py tests/test_demo_nav.py tests/test_design_prompts.py tests/test_apt_dev_hub.py -q
- Contracts are pinned: 04-spec/contracts/*.md win over any other doc. Real Gate, no mocks of decision logic. Offline default $0.
- Report compactly: files, exact test counts, branch name, commit hash, deviations+reasons.
