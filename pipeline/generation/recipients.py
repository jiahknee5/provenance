"""Synthetic recipients — the 1000 "form submissions," seeded and reproducible.

Distributed across 8 micro-segments (role x size-tier). The same Recipient model backs the
live web form, so a real submission and a generated one are identical downstream.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone

from pipeline.common import config
from pipeline.common.config import USERS_PATH
from pipeline.common.db import connect, init_db
from pipeline.common.schemas import Recipient

ROLES = ["clinops", "cfo", "it_security", "quality"]
ROLE_WEIGHTS = [0.32, 0.26, 0.24, 0.18]
SIZES = ["community", "regional", "idn"]
SIZE_WEIGHTS = [0.35, 0.35, 0.30]
REGIONS = ["Northeast", "Midwest", "South", "West"]
URGENCY = ["low", "medium", "high"]
URGENCY_WEIGHTS = [0.3, 0.5, 0.2]
HEARD = ["webinar", "referral", "conference", "search", "analyst report"]

ROLE_TITLES = {
    "clinops": "VP Clinical Operations", "cfo": "Chief Financial Officer",
    "it_security": "Director of IT Security", "quality": "Chief Quality Officer",
}
ROLE_USE_CASES = {
    "clinops": "reduce length of stay", "cfo": "lower total cost of ownership",
    "it_security": "secure EHR integration", "quality": "improve outcome reporting",
}
FIRST = ["Maya", "David", "Priya", "James", "Aisha", "Daniel", "Elena", "Marcus",
         "Sofia", "Liam", "Nina", "Omar", "Grace", "Ethan", "Lena", "Carlos"]
LAST = ["Chen", "Patel", "Rivera", "Okafor", "Kim", "Nguyen", "Santos", "Walsh",
        "Ahmed", "Brooks", "Romano", "Larsen", "Diaz", "Foster", "Haddad", "Mori"]
SYS_A = ["Northwind", "Cedar Valley", "Lakeshore", "Summit", "Riverbend", "Harbor",
         "Pinecrest", "Granite", "Meadowbrook", "Bayview"]
SYS_B = ["Health", "Medical Center", "Hospital System", "Care Network", "Regional Health"]


def tier(size: str) -> str:
    return "ent" if size == "idn" else "core"


def segment(role: str, size: str) -> str:
    return f"{role}__{tier(size)}"


ALL_SEGMENTS = [f"{r}__{t}" for r in ROLES for t in ("core", "ent")]


def generate(n: int = 1000, seed: int | None = None) -> list[Recipient]:
    rng = random.Random(seed if seed is not None else config.SEED)
    out: list[Recipient] = []
    for i in range(n):
        role = rng.choices(ROLES, ROLE_WEIGHTS)[0]
        size = rng.choices(SIZES, SIZE_WEIGHTS)[0]
        first, last = rng.choice(FIRST), rng.choice(LAST)
        company = f"{rng.choice(SYS_A)} {rng.choice(SYS_B)}"
        slug = company.lower().replace(" ", "")
        out.append(Recipient(
            recipient_id=f"r{i:04d}",
            token=format(rng.getrandbits(64), "016x"),
            name=f"{first} {last}",
            email=f"{first.lower()}.{last.lower()}@{slug}.org",
            company=company,
            role=role,
            company_size=size,
            region=rng.choice(REGIONS),
            use_case=ROLE_USE_CASES[role],
            urgency=rng.choices(URGENCY, URGENCY_WEIGHTS)[0],
            consent=True,
            heard_via=rng.choice(HEARD),
            segment=segment(role, size),
            created_at=datetime.now(timezone.utc).isoformat(),
        ))
    return out


def save(recipients: list[Recipient]) -> None:
    init_db()
    conn = connect()
    try:
        conn.execute("DELETE FROM recipients;")
        conn.executemany(
            "INSERT INTO recipients (recipient_id, token, payload, created_at) VALUES (?,?,?,?)",
            [(r.recipient_id, r.token, r.model_dump_json(), r.created_at) for r in recipients])
        conn.commit()
    finally:
        conn.close()
    USERS_PATH.write_text("\n".join(r.model_dump_json() for r in recipients))


def load_all() -> list[Recipient]:
    conn = connect()
    try:
        rows = conn.execute("SELECT payload FROM recipients ORDER BY recipient_id").fetchall()
    finally:
        conn.close()
    return [Recipient.model_validate_json(r["payload"]) for r in rows]


def by_token(token: str) -> Recipient | None:
    conn = connect()
    try:
        row = conn.execute("SELECT payload FROM recipients WHERE token=?", (token,)).fetchone()
    finally:
        conn.close()
    return Recipient.model_validate_json(row["payload"]) if row else None


def insert_one(r: Recipient) -> None:
    """Used by the live web form."""
    init_db()
    conn = connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO recipients (recipient_id, token, payload, created_at) VALUES (?,?,?,?)",
            (r.recipient_id, r.token, r.model_dump_json(), r.created_at))
        conn.execute("INSERT INTO form_events (recipient_id, ts, payload) VALUES (?,?,?)",
                     (r.recipient_id, r.created_at, r.model_dump_json()))
        conn.commit()
    finally:
        conn.close()
