"""Evidence retriever — hybrid lexical retrieval over the Library's current sentences.

Always indexes the *live* source text (rebuilds when the library version changes), so a
re-Gate after a source change retrieves the new sentence — which is how a number-drifted
source flips a previously-green claim to red.
"""
from __future__ import annotations

from typing import Optional

from rank_bm25 import BM25Okapi

from pipeline.common import textutil
from pipeline.library.library import ClaimsLibrary


class Retriever:
    def __init__(self, library: ClaimsLibrary):
        self.library = library
        self._version: Optional[str] = None
        self._corpus: list[dict] = []
        self._bm25: Optional[BM25Okapi] = None
        self._rebuild()

    def _rebuild(self) -> None:
        self._corpus = self.library.evidence_sentences()
        tokenized = [textutil.tokenize(c["text"]) for c in self._corpus]
        self._bm25 = BM25Okapi(tokenized)
        self._version = self.library.library_version()

    def retrieve(self, claim_text: str, k: int = 1) -> list[dict]:
        if self._version != self.library.library_version():
            self._rebuild()
        scores = self._bm25.get_scores(textutil.tokenize(claim_text))
        ranked = sorted(range(len(self._corpus)), key=lambda i: scores[i], reverse=True)
        out = []
        for i in ranked[:k]:
            c = dict(self._corpus[i])
            c["score"] = float(scores[i])
            out.append(c)
        return out
