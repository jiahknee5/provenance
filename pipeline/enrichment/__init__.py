"""Enrichment lane — data-provenance, the mirror of the claim Gate.

A profile fact is bound to its source connector, carries a lawful basis + freshness TTL,
passes the Enrichment Gate (usable / disclaimer / blocked), and is audited by the Assurance
Lab. Blocked facts never reach a message. See docs/04-workflow/ENRICHMENT-TOUCHPOINTS.md.
"""
