"""UI-consistency harness (SPEC §E / §6) — the gate the /loop runs to until green.

Asserts every navigable surface of the restructured app:
  1. renders (200),
  2. extends the Quiet-Workspace shell,
  3. carries the shell markers (sidebar + topbar),
  4. uses ONLY token colours (no raw hex in the template — all colour via var(--…)).

Run:  python -m scripts.ui_consistency   (exit 0 = consistent)
"""
from __future__ import annotations

import pathlib
import re
import sys

from starlette.testclient import TestClient

from app.main import app

TPL = pathlib.Path(__file__).resolve().parents[1] / "app" / "templates"
SHELL_PAGES = ["workspace", "records", "records_new", "agent", "assurance", "optimizer",
               "sources", "composer", "demo", "demo_monitor", "policies", "graph"]
ROUTES = ["/workspace", "/records", "/records/new", "/agent", "/assurance", "/optimizer",
          "/sources", "/composer", "/demo", "/demo/monitor", "/policies", "/graph"]
_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def main() -> int:
    c = TestClient(app)
    problems: list[str] = []

    for route in ROUTES:
        r = c.get(route)
        if r.status_code != 200:
            problems.append(f"{route}: HTTP {r.status_code}")
        elif 'class="q-app"' not in r.text or 'class="q-side"' not in r.text:
            problems.append(f"{route}: missing shell markers (sidebar/topbar)")

    for name in SHELL_PAGES + ["shell"]:
        body = (TPL / f"{name}.html").read_text()
        if name != "shell" and 'extends "shell.html"' not in body:
            problems.append(f"{name}.html: does not extend the shell")
        raw = sorted(set(_HEX.findall(body)))
        if raw:
            problems.append(f"{name}.html: off-token raw hex {raw}")

    if problems:
        print("UI CONSISTENCY: FAIL")
        for p in problems:
            print("  ✗", p)
        return 1
    print(f"UI CONSISTENCY: PASS — {len(ROUTES)} shell surfaces extend the shell, token-only colour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
