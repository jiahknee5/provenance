"""The Claims Library — versioned claim-evidence graph + source registry.

Born here (not bolted on for Drift): every ClaimNode carries the `source_version` it was
verified against, and `claims_for_source()` is the dependency edge the Drift Monitor walks
when a source changes. A claim is "drifted" when its `source_version` no longer matches
the registry's current version for its source — the Gate then re-verifies it against the
new text.
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional

from pipeline.common.config import CLAIMS_DIR
from pipeline.common.schemas import ClaimNode, ClaimStatus, SourceDoc
from pipeline.library import seed_data


def _sentences(text: str) -> list[tuple[int, str]]:
    """Split into sentences, returning (start_offset, sentence)."""
    out, i = [], 0
    for part in text.split(". "):
        out.append((i, part.strip(". ")))
        i += len(part) + 2
    return out


class ClaimsLibrary:
    def __init__(self, sources: list[SourceDoc], claims: list[ClaimNode]):
        self.sources: dict[str, SourceDoc] = {s.source_id: s for s in sources}
        self.claims: dict[str, ClaimNode] = {c.claim_id: c for c in claims}

    # ---- construction ------------------------------------------------------
    @classmethod
    def from_seed(cls) -> "ClaimsLibrary":
        sources = [SourceDoc(source_id=s["source_id"], title=s["title"], text=s["text"])
                   for s in seed_data.SOURCES]
        src_by_id = {s.source_id: s for s in sources}
        claims = []
        for c in seed_data.CLAIMS:
            src = src_by_id[c["source_id"]]
            start = src.text.find(c["evidence"])
            if start < 0:
                raise ValueError(f"evidence for {c['claim_id']} not found in {c['source_id']}: "
                                 f"{c['evidence']!r}")
            claims.append(ClaimNode(
                claim_id=c["claim_id"], text=c["text"], source_id=c["source_id"],
                span=(start, start + len(c["evidence"])), source_version=src.source_version,
                status=ClaimStatus.IN_DATE, numeric=c["numeric"], numeric_unit=c["numeric_unit"],
                segments=c["segments"], rule_tags=c["rule_tags"],
            ))
        return cls(sources, claims)

    # ---- queries -----------------------------------------------------------
    def claims_in_date(self) -> list[ClaimNode]:
        return [c for c in self.claims.values() if c.status == ClaimStatus.IN_DATE]

    def claims_for_segment(self, role: str) -> list[ClaimNode]:
        return [c for c in self.claims_in_date() if not c.segments or role in c.segments]

    def claim(self, claim_id: str) -> Optional[ClaimNode]:
        return self.claims.get(claim_id)

    def claim_text_map(self) -> dict[str, str]:
        return {cid: c.text for cid, c in self.claims.items()}

    def source(self, source_id: str) -> SourceDoc:
        return self.sources[source_id]

    def source_version(self, source_id: str) -> str:
        return self.sources[source_id].source_version

    # ---- the dependency graph (claim -> source) ----------------------------
    def claims_for_source(self, source_id: str) -> list[str]:
        return [cid for cid, c in self.claims.items() if c.source_id == source_id]

    def is_drifted(self, claim_id: str) -> bool:
        c = self.claims[claim_id]
        return c.source_version != self.sources[c.source_id].source_version

    # ---- evidence (for the Gate's retriever) -------------------------------
    def evidence_sentences(self) -> list[dict]:
        """Current source sentences — the retrieval corpus (rebuilt from live text)."""
        corpus = []
        for s in self.sources.values():
            for off, sent in _sentences(s.text):
                if sent:
                    corpus.append({"source_id": s.source_id, "source_version": s.source_version,
                                   "offset": off, "text": sent})
        return corpus

    def bound_evidence(self, claim_id: str) -> str:
        c = self.claims[claim_id]
        return self.sources[c.source_id].text[c.span[0]:c.span[1]]

    # ---- versioning --------------------------------------------------------
    def library_version(self) -> str:
        h = hashlib.sha256()
        for sid in sorted(self.sources):
            h.update(f"{sid}:{self.sources[sid].source_version}".encode())
        for cid in sorted(self.claims):
            h.update(cid.encode())
        return "lib_" + h.hexdigest()[:12]

    # ---- drift trigger: a source changed -----------------------------------
    def apply_source_change(self, source_id: str, new_text: str) -> list[str]:
        """Update a source's text (-> new version). Returns the claim_ids that depend on
        it (the surgical re-verification set the Drift Monitor will re-Gate). Claim nodes
        keep their stale `source_version` until the Gate re-verifies them."""
        old = self.sources[source_id]
        self.sources[source_id] = SourceDoc(source_id=source_id, title=old.title, text=new_text)
        return self.claims_for_source(source_id)

    def mark_verified(self, claim_id: str) -> None:
        """After a re-Gate, the claim now depends on the current source version."""
        c = self.claims[claim_id]
        c.source_version = self.sources[c.source_id].source_version

    # ---- persistence -------------------------------------------------------
    def save(self) -> None:
        (CLAIMS_DIR / "library.json").write_text(json.dumps({
            "sources": {sid: s.model_dump() for sid, s in self.sources.items()},
            "claims": {cid: c.model_dump() for cid, c in self.claims.items()},
            "library_version": self.library_version(),
        }, indent=2, default=str))

    @classmethod
    def load(cls) -> "ClaimsLibrary":
        raw = json.loads((CLAIMS_DIR / "library.json").read_text())
        sources = [SourceDoc(**s) for s in raw["sources"].values()]
        claims = [ClaimNode(**c) for c in raw["claims"].values()]
        return cls(sources, claims)
