"""Seed data for the demo tenant **Helix Analytics** — a regulated health-tech firm
selling clinical-ops ROI analytics to hospitals.

Four approved source documents and the ten atomic claims bound to them. Each claim names
the exact evidence substring it is bound to (the span is computed, not hand-counted), the
number it asserts (what number-drift mutates), the compliance tags the rules engine keys
on, and the role micro-segments it is most relevant to.

c_tco (the 47% TCO claim) is the one the MLR legal hold flips on — the legal-hold demo.
"""
from __future__ import annotations

# --- approved source documents ---------------------------------------------
SOURCES: list[dict] = [
    {
        "source_id": "s_casestudy",
        "title": "Northwind Health — deployed case study",
        "text": (
            "In an 18-month deployment, Northwind Health cut total cost of ownership by 47%. "
            "The system reduced average length of stay by 1.2 days. "
            "Helix Analytics is now deployed across 12 hospital systems."
        ),
    },
    {
        "source_id": "s_datasheet",
        "title": "Helix Analytics — product data sheet",
        "text": (
            "The platform processes a full claims dataset in under 4 hours. "
            "It integrates with 30 EHR systems out of the box. "
            "Helix Analytics is SOC 2 Type II certified."
        ),
    },
    {
        "source_id": "s_pricing",
        "title": "Helix Analytics — pricing fact sheet",
        "text": (
            "Helix Analytics is priced at $0.12 per patient record. "
            "There is no implementation fee for systems under 200 beds."
        ),
    },
    {
        "source_id": "s_security",
        "title": "Helix Analytics — security & compliance overview",
        "text": (
            "Helix Analytics is HIPAA compliant. "
            "All data is encrypted at rest and in transit."
        ),
    },
]

# --- approved claims (canonical text, bound evidence substring, metadata) ----
# fields: claim_id, text (citable), source_id, evidence (exact substring of the source),
#         numeric, numeric_unit, rule_tags, segments (roles it's most relevant to)
CLAIMS: list[dict] = [
    {"claim_id": "c_tco", "text": "cuts total cost of ownership by 47%",
     "source_id": "s_casestudy", "evidence": "Northwind Health cut total cost of ownership by 47%",
     "numeric": 47.0, "numeric_unit": "%", "rule_tags": ["roi_outcome"], "segments": ["cfo"]},
    {"claim_id": "c_los", "text": "reduces average length of stay by 1.2 days",
     "source_id": "s_casestudy", "evidence": "reduced average length of stay by 1.2 days",
     "numeric": 1.2, "numeric_unit": "day", "rule_tags": ["clinical_outcome"], "segments": ["clinops", "quality"]},
    {"claim_id": "c_deployed", "text": "is deployed across 12 hospital systems",
     "source_id": "s_casestudy", "evidence": "deployed across 12 hospital systems",
     "numeric": 12.0, "numeric_unit": "", "rule_tags": ["proof"], "segments": []},
    {"claim_id": "c_speed", "text": "processes a full claims dataset in under 4 hours",
     "source_id": "s_datasheet", "evidence": "processes a full claims dataset in under 4 hours",
     "numeric": 4.0, "numeric_unit": "hour", "rule_tags": ["performance"], "segments": ["clinops", "it_security"]},
    {"claim_id": "c_ehr", "text": "integrates with 30 EHR systems",
     "source_id": "s_datasheet", "evidence": "integrates with 30 EHR systems",
     "numeric": 30.0, "numeric_unit": "", "rule_tags": ["integration"], "segments": ["it_security"]},
    {"claim_id": "c_soc2", "text": "is SOC 2 Type II certified",
     "source_id": "s_datasheet", "evidence": "SOC 2 Type II certified",
     "numeric": None, "numeric_unit": "", "rule_tags": ["security"], "segments": ["it_security"]},
    {"claim_id": "c_price", "text": "is priced at $0.12 per patient record",
     "source_id": "s_pricing", "evidence": "priced at $0.12 per patient record",
     "numeric": 0.12, "numeric_unit": "", "rule_tags": ["pricing"], "segments": ["cfo"]},
    {"claim_id": "c_nofee", "text": "has no implementation fee for systems under 200 beds",
     "source_id": "s_pricing", "evidence": "no implementation fee for systems under 200 beds",
     "numeric": 200.0, "numeric_unit": "", "rule_tags": ["pricing"], "segments": ["cfo"]},
    {"claim_id": "c_hipaa", "text": "is HIPAA compliant",
     "source_id": "s_security", "evidence": "HIPAA compliant",
     "numeric": None, "numeric_unit": "", "rule_tags": ["security"], "segments": []},
    {"claim_id": "c_encrypt", "text": "encrypts all data at rest and in transit",
     "source_id": "s_security", "evidence": "encrypted at rest and in transit",
     "numeric": None, "numeric_unit": "", "rule_tags": ["security"], "segments": ["it_security"]},
]

# the planted lie — an unverifiable, guaranteed-outcome claim that is NOT in the approved
# set. Generation can inline it into a variant; the Gate must block it (number unsupported
# by any source + 'guarantee' compliance rule). Never added to the Library.
PLANTED_LIE_TEXT = "guarantees a 60% reduction in hospital readmissions"
