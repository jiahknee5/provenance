"""Headline property T1 — the truth-bounded optimizer can't win by lying.

The proof is a contrast on identical data/oracle: the Gate-constrained bandit never
selects the planted lie (it isn't in the pool) and converges to the best honest arm; the
unconstrained twin converges to the lie. Same recipients, same oracle, only the truth
boundary differs.
"""
from __future__ import annotations

import os
import subprocess
import sys

from pipeline.common.config import PROJECT_ROOT
from pipeline.common.store import PosteriorStore
from pipeline.generation import recipients
from pipeline.generation.variants import build_action_pool
from pipeline.optimizer import oracle
from pipeline.optimizer.campaign import run_campaign
from pipeline.optimizer.oracle import preferred_arm

SEED = 100


def test_oracle_is_reproducible_across_processes():
    """The oracle must not depend on Python's salted builtin hash() — otherwise the demo
    is not reproducible across runs (a real bug we fixed)."""
    code = ("from pipeline.optimizer.oracle import latent_ctr;"
            "print(latent_ctr('cfo__core','cfo__core__email__A'))")
    outs = set()
    for seed in ("0", "1", "random"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           env=env, cwd=str(PROJECT_ROOT))
        outs.add(r.stdout.strip())
    assert len(outs) == 1, f"latent_ctr varies by PYTHONHASHSEED: {outs}"


def test_oracle_lie_has_highest_latent_ctr():
    seg = "cfo__core"
    assert oracle.latent_ctr(seg, f"{seg}__email__LIE") > oracle.latent_ctr(seg, f"{seg}__email__A")
    assert oracle.latent_ctr(seg, f"{seg}__email__LIE") > oracle.latent_ctr(seg, f"{seg}__email__B")


def test_t1_constrained_bandit_never_selects_the_lie(gate):
    recips = recipients.generate(1000)
    pool, report = build_action_pool(gate, "email", "c1_test", constrained=True)
    # the lie is structurally absent from the pool
    assert not any(v.endswith("__LIE") for v in pool.all_variant_ids())
    t = run_campaign("email", "c1_test", recips, pool, PosteriorStore("c1_test", "email"),
                     constrained=True, seed=SEED, log_db=False)
    assert t["selections_of_lie"] == 0
    assert not t["winner_is_lie_anywhere"]
    # and it converges to the best honest arm in (nearly) every segment
    conv = sum(1 for seg, s in t["per_segment"].items()
               if s["winner"] == f"{seg}__email__{preferred_arm(seg)}")
    assert conv >= 7


def test_t1_unconstrained_twin_converges_to_the_lie(gate):
    recips = recipients.generate(1000)
    pool, _ = build_action_pool(gate, "email", "twin_test", constrained=False)
    assert any(v.endswith("__LIE") for v in pool.all_variant_ids())   # lie IS in this pool
    t = run_campaign("email", "twin_test", recips, pool, PosteriorStore("twin_test", "email"),
                     constrained=False, seed=SEED, log_db=False)
    assert t["selections_of_lie"] > 0
    lie_winners = sum(1 for s in t["per_segment"].values() if s["winner_is_lie"])
    assert lie_winners >= 6
