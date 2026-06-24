"""Deterministic agent — navigates the optimizer / assurance / drift state (SPEC §C).

$0, offline, provable: every answer is computed from the real engine artifacts and
carries its provenance. No LLM in the default path; an optional NL→intent router can be
layered on top (key-gated) without changing what the intents actually do.
"""
