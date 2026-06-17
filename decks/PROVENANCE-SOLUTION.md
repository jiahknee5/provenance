Provenance · The packaged solution

# The system of record for every claim your marketing makes

One object ties the whole thing together — the **claim**. Provenance tracks every claim from the moment it's written to the moment it expires, and can prove it at any point. Generation, verification, optimization, compliance, and monitoring stop being separate features; they're **stages in a claim's life.**

General ledger = system of record for **money** CRM = system of record for **customers** Provenance = system of record for **claims**

## Where it sits in the marketing stack

It doesn't replace your tools — it sits in front of "send" as the claim firewall.

Marketing already has tools to write, target, and send. What it lacks is a layer that decides **what you're allowed to say, to whom, with proof.** Provenance ingests your truth (and your prospects), governs every claim, and only then lets the message flow to the channels you already use.

Ingests — your sources of truth + your prospects

Product & spec docsClinical / trial dataCase studiesPricing sheetsApproved-claims & legal holdsCRM / CDP (prospect facts)

▼ feeds

The system of record

Provenance — the Claims Library + the 7-stage engine

A living database of every claim, its source, its status, and its performance — plus the engine that drafts, verifies, clears, optimizes, sends, monitors, and proves.

DraftVerifyClearOptimizeSendMonitorProve

▼ governs every outbound message

Flows to — the channels you already run

Email / ESP (HubSpot, Marketo, Klaviyo)Sales engagement (Outreach, Salesloft)AdsCMS / webSocial

## The core object — a claim record

"System of record" is literal: every claim is a row you can query, audit, and trust.

CLAIM #4471

text"saves ~$10 per head"

sourceApproved Economics Sheet v3 (Apr 2026)

verified✓ entailed · NLI 0.94 + semantic ✓

sayable✓ cleared · rule "ROI-claims-OK"

ownerProduct Marketing

expireson source change · review Oct 2026

used in1,240 sends · 7.2% reply (feedlot)

**This row is the unit of everything.** It's what gets verified, what the optimizer chooses between, what gets re-checked when a source changes, and what an auditor pulls when a regulator asks "why did you say that?"

The **Claims Library** is the collection of these rows — the company's single source of truth for *what it is allowed to say.* It's the asset that compounds: every campaign and client adds verified rows, and a competitor starting from zero can't catch up.

## A claim's life — seven stages, concretely

Born → papers checked → cleared to travel → competes to win → ships with a receipt → re-checked when the world changes → the whole border audited.

Running example: outreach to **Iowa feedlot managers, 1,000+ head**, for a rice-expressed lysozyme feed product (our live domain). The same lifecycle runs for a pharma rep email, a fintech nurture sequence, or a SaaS cold campaign.

Stage 1

Drafted

A marketer launches a campaign to a segment in their normal tool, or the engine proposes variants. Provenance pulls the prospect's facts from the CRM/CDP and drafts a personalized message, drawing only from the Claims Library. It then **splits the draft into atomic claims.**

ExampleDraft: "At your 4,000 head, LysoSure saves ~$10/head and is egg-allergen-free." → claims: **[4,000 head]** · **[saves ~$10/head]** · **[egg-allergen-free]**.

**Who:** Marketer (one click) · **Sees:** a draft with claims itemized beneath it.

Stage 2

Sourced & verified

Each claim is bound to a source record and confirmed by **two independent checks** — a literal "does the document say this?" check, then a meaning check — with a cheap pass first and only the uncertain claims escalated to the heavier ensemble (keeps it affordable per message).

Example"4,000 head" ↦ EPA permit #IA-0421 (exact). "saves ~$10/head" ↦ economics sheet (entailed). "egg-allergen-free" ↦ product spec (entailed). All **green**, each with a clickable citation.

**Who:** automatic · **Sees:** green checks; click any to see the exact source line.

Stage 3

Cleared (compliance / "sayable")

Verified ≠ allowed. Each claim runs against the **claimability rules** Legal authored once. A claim can be perfectly true and still blocked — legal hold, jurisdiction, channel, or required disclaimer.

ExampleA "**cuts feed 13%**" claim is true and sourced — but a rule says "UTK trial data under legal hold." It turns **red**, with the reason. The marketer can't override it; only Legal can lift the rule.

**Who:** rules set by Legal/Compliance once · **Sees:** red + plain-English reason.

Stage 4

Optimized

For each segment, the engine auto-A/B-tests **verified, cleared** variants — which claim to lead with, the framing, channel, and send time — and shifts toward what converts. Because only cleared claims compete, **it can't learn to win by exaggerating.**

ExampleFor feedlot managers, "lead with $/head ROI" beats "lead with allergen-free" ~2:1 → adopted automatically. For nutritionists (influencers), the peer/mechanism angle wins instead.

**Who:** automatic · **Sees:** a live per-segment leaderboard — no test setup required.

Stage 5

Sent (with a receipt)

The approved message is pushed to the channel you already use, bundled with its citations, and an **immutable audit record** is written: what was claimed, sourced to what, cleared by which rule, optimized how, and when.

ExampleEmail goes out via Outreach. If a regulator or a prospect ever asks "where did you get that?", the answer is one click — proof, not vibes.

**Who:** automatic · **Sees:** Sales/Marketing send as normal; the audit trail accrues silently.

Stage 6

Monitored (claims go stale)

A verified claim is only true until its source changes. Provenance watches the sources and **re-verifies dependent claims** when something shifts — pausing or unblocking sends automatically.

ExamplesLegal lifts the UTK hold → "13% feed" **auto-unblocks everywhere.** A permit drops 4,000 → 2,000 head → every email still saying "4,000" is **paused for re-check.** A reference customer churns → "trusted by ACME" is **pulled.**

**Who:** automatic · **Sees:** drift alerts; the library stays true with no manual re-audit.

Stage 7

Proven (continuous assurance)

The checker itself is held to account. Provenance continuously runs **adversarial traps** (true claims mutated into subtle lies) and reports a reliability profile — not one number — so trust is something you can show a board or an auditor.

Example"This quarter the gate caught **98.7%** of planted false claims at a **2.1%** false-reject rate, calibrated within ±3%." A trust dashboard, not a promise.

**Who:** automatic · **Sees:** CMO / Legal / board get an audit-ready assurance report.

## The shift it creates in how marketing works

Review moves from per-asset to per-rule — the bottleneck disappears.

Today, in any claims-heavy business, legal/compliance reviews *every asset* — a serial queue that kills personalization at scale. Provenance flips it: Legal approves the **claims library and the rules once**, and every generated message is checked against them **continuously and instantly.**

Today — per-asset review

Every email / ad / variant queues for legal.

Days-to-weeks of lag; review repeated for each variant.

Personalization dies — you ship one safe generic version.

When it goes wrong, no record of why it was allowed.

With Provenance — per-rule governance

Legal approves the **claims library + rules once.**

Every message auto-checked **instantly,** at any volume.

**1:1 personalization at scale** — every variant is pre-cleared.

Full **audit trail** by default — defensible to regulators.

## Who touches it, and what changes for them

Marketer

Launches campaigns and sees green / amber / red per claim. **Never waits in a review queue;** ships personalized outreach in minutes.

Legal / Compliance (MLR)

Authors the claims library + rules **once,** then monitors the assurance dashboard. **Stops reviewing every asset** — governs the system, not each email.

RevOps / Marketing Ops

Owns segments, the integrations into ESP/CRM, and the optimization settings. Gets a single source of truth for what's claimable.

Sales

Sends verified, personalized outreach knowing every line is backed — and can show the source if a prospect pushes back.

**The one solution:** a system of record for claims. Every claim is a tracked row with a chain of custody — drafted, verified, cleared, optimized, sent, monitored, and proven. Generation and truth-bounded optimization are just the front and back halves of that lifecycle; verification rigor, source-drift, and the cost cascade are how each stage is made trustworthy.

Provenance · solution detail · Jun 15 2026. Companion: [beyond marketing](BEYOND-MARKETING.html) · [big picture](THE-BIG-PICTURE.html) · [funnel + big tech](FULL-FUNNEL-VIEW.html) · [hub](index.html).
