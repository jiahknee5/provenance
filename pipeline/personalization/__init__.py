"""Super-personalization, provenance-first.

The question this answers: *how much could a website know about you the instant it
loads — and where would each fact come from?* Every personalization signal here is bound
to a **provenance** (observed / declared / Google-OAuth / purchased-from-a-broker /
first-party DB / identity-graph), a real-world **vendor + acquisition method**, a **cost**,
a **lawful basis**, and a **surface policy** (the same say/allude/hold control the funnel
uses). Tasteful mode honours the surface policy; the "creepy" mode switches it off and
shows *everything available* — each line still tagged with exactly where it came from.

Data is synthesized for one deterministic persona; nothing here calls a paid API.
"""
