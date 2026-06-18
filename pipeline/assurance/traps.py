"""Adversarial-trap generator — mutate verified claims into labeled traps.

Four mutation operators, each a way a claim can be false-or-unsayable while looking fine
to a shallow judge:
  * number_drift          — change the asserted number (47% -> 57%). Nearly identical
                            lexically; a similarity judge passes it.
  * unsupported_superlative — inject "#1 / best-in-class" not in any source.
  * false_equivalence     — append an unsubstantiated competitor comparison.
  * true_but_unsayable    — a TRUE stat wrapped in a guarantee (entailed but impermissible).
Plus the clean approved claims (label 0) for measuring false-reject.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.library.library import ClaimsLibrary


@dataclass
class Trap:
    trap_id: str
    text: str
    mutation: str          # number_drift | unsupported_superlative | false_equivalence |
                           # true_but_unsayable | clean
    label: int             # 1 = should be caught (red), 0 = clean (should pass)
    severity: str          # material | puffery | clean
    source_claim_id: str


def _drift_number(text: str, value: float) -> str:
    new = str(int(value + 10)) if float(value).is_integer() else str(round(value * 1.4, 2))
    return re.sub(r"\d+(?:\.\d+)?", new, text, count=1)


def generate(library: ClaimsLibrary) -> list[Trap]:
    traps: list[Trap] = []
    claims = library.claims_in_date()

    for c in claims:
        # clean control (verbatim approved claim)
        traps.append(Trap(f"clean_{c.claim_id}", f"Helix Analytics {c.text}.",
                          "clean", 0, "clean", c.claim_id))
        # number drift (only for numeric claims) — the subtle material trap
        if c.numeric is not None:
            traps.append(Trap(f"num_{c.claim_id}",
                              f"Helix Analytics {_drift_number(c.text, c.numeric)}.",
                              "number_drift", 1, "material", c.claim_id))
        # unsupported superlative
        traps.append(Trap(f"sup_{c.claim_id}",
                          f"Helix Analytics is the #1 best-in-class platform and {c.text}.",
                          "unsupported_superlative", 1, "puffery", c.claim_id))
        # false equivalence / competitor disparagement
        traps.append(Trap(f"fe_{c.claim_id}",
                          f"Helix Analytics {c.text}, far better than Epic and Cerner.",
                          "false_equivalence", 1, "material", c.claim_id))
        # true-but-unsayable (entailed stat wrapped in a guarantee)
        traps.append(Trap(f"tbu_{c.claim_id}",
                          f"We guarantee that Helix Analytics {c.text}.",
                          "true_but_unsayable", 1, "material", c.claim_id))
    return traps
