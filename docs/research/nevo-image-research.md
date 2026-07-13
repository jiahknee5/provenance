# NEVO → hero-image research memo

> **Deliverable:** research memo only. No application code, pipeline, rules, or tests were
> changed. This memo maps findings from the EPFL **NEvo** project to our hero-image
> personalization pipeline (`pipeline/personalization/image_intents.py`, `rules/*_image.yaml`,
> `docs/04-workflow/ACTION-IMAGE-PERSONALIZATION.md`) and proposes *candidate* (not implemented)
> tenant-YAML additions.
>
> **Read date:** 2026-07-09. Sources: NEvo project site, arXiv preprint, Hugging Face model card,
> EPFL NeuroAI Lab page (full citations in §6).
>
> **Companion:** a longer dossier already exists at
> [`nevo-neuroadaptive-imaging-research.md`](nevo-neuroadaptive-imaging-research.md) (covers the
> MindPilot EEG sister-work and the off-the-shelf predictor landscape). This memo is the focused,
> action-oriented version scoped to the task: *can we match our image goals to
> brain-stimulation / neuroscience findings?*
>
> **Discipline:** treat NEvo's *mechanisms* (which visual features drive which region) as
> load-bearing and its *magnitudes* skeptically. Every number NEvo reports is a **predicted**
> neural activation under one encoder — not a measured human response, and never a
> "this image converts X%" claim. The authors say so explicitly.

---

## 1. What NEVO actually is

**NEvo = "Neural-Guided Evolutionary Video Synthesis for Dynamic Visual Selectivity"** (Tang,
Salehi, Zhou, Zamir, Isik, Schrimpf — EPFL NeuroAI Lab + Johns Hopkins; arXiv 2607.02317).

It is a **basic-neuroscience probing tool, not a marketing tool.** It answers one question:
*"what kind of video would make a given part of your visual brain light up the most?"* It does
this **in silico** — no human is in the loop at generation time.

The method is a four-part loop (paper §3):

1. **Structured "gene" prompt space.** Each candidate video is described by discrete genes across
   ~30 image-attribute categories (614 options) and ~11 motion categories (163 options), grouped
   by visual-hierarchy level: low-level (pattern, spatial frequency, edge density, color, texture),
   mid/high (object form, body content/action, face content, scene category/geometry), social
   (social dynamics, social cue, intention signal, agent number), motion (motion strength, rhythm,
   interaction, event structure, camera motion), plus coherence anchors (mood, style, lighting,
   framing).
2. **Generator `G`.** SDXL-Turbo for the still-image stage, LTX-Video for the 2-second animation.
3. **Scorer `S` — a "digital twin" of the brain.** V-JEPA 2 video features → voxel-wise ridge
   regression to fMRI, trained on public video-fMRI datasets (BOLDMoments + a social-interaction
   set). ROI score = mean predicted response over the region's voxels.
4. **Evolutionary search.** Population 20, keep top 30% as elites, crossover 0.5, per-gene mutation
   0.2, run in two stages (find the best still image first, then optimize motion).

### 1.1 Citable findings relevant to us (and honest limits)

**What is established / defensible (direction, not magnitude):**

- **NEvo recovers known regional selectivity.** Optimizing for a region reliably produces the
  content that region is known to prefer: **faces → FFA, scenes/places → PPA, bodies → EBA,
  coherent motion → MT/V3A, social interaction → pSTS/aSTS** (§4.1, Fig. 3A). This is a *replication*
  of decades of mainstream vision science (Kanwisher et al. 1997 on FFA; Epstein et al. 1999 on PPA;
  Pitcher & Ungerleider 2021 on the social/lateral pathway), so it is safe to lean on.
- **A feature hierarchy runs from low-level to social.** A searchlight sweep from early visual
  cortex (V1) to anterior STS shows a smooth gradient: **high-contrast texture/pattern → motion →
  bodies → dyadic physical interaction → face-to-face social contact** (§4.4, Fig. 5A).
- **Property→activation correlations (their Fig. 5B / Tab. S7), the most directly reusable result.**
  On 0–10 human-annotated properties: biological motion correlates with MT activation (r ≈ 0.84,
  p < 0.001), joint action with pSTS (r ≈ 0.73, p < 0.001); face and body presence sit at the high
  end across face/body/social regions. Read-across for a static hero: **faces > human bodies >
  implied motion > social configuration > open scene/depth > raw texture**, as an
  attention/engagement ordering.
- **One dominant driver per image.** NEvo's whole objective presumes a single region-defining driver;
  this backs our existing `"single focal point — processing fluency"` principle.
- **Text/pattern is a low-level distractor.** Dense high-contrast texture grabs *early* visual cortex
  but carries no higher-order meaning — supports our "NO text in image" guardrail (text competes for
  the same fixation budget the headline needs).

**What is NOT established (do not overclaim):**

- NEvo studies **neural activation, not persuasion, emotion, purchase, or conversion.** It has
  **no valence/arousal model and no behavioral outcome.** Any "arousal/valence" framing in this memo
  is imported from adjacent affect literature (and the MindPilot EEG work in the companion dossier),
  **not** from NEvo.
- Every NEvo number is a **prediction under one encoder.** The authors explicitly warn that results
  "reflect both neural selectivity and encoder bias" and are "predictions to validate in vivo, not
  ground truth," and that optimizing hard against a single encoder **exploits its artifacts**.
- NEvo is **video and dynamic**; our heroes are **static**. The motion findings transfer only as
  *implied* motion (a frozen mid-action frame), which is weaker than real motion in their own data.
- It requires a **CUDA GPU + 13B video model + fMRI-trained encoder.** None of it is a live web
  component.

**Bottom line on NEvo itself:** the *transferable asset is the architecture* — `structured gene
space → generator → predicted-response scorer → bounded search` — plus a *feature-hierarchy evidence
base*. The brain-encoding model is not something we deploy.

---

## 2. Concrete mapping: our conversion goals/intents → neuroscience-grounded visual attributes

Our current intents already encode good instincts (single focal point, faceless human silhouettes,
industry-matched environment, dark base with a gold accent zone kept clear for the headline). The
NEvo feature hierarchy lets us make those instincts **explicit and inspectable** rather than
implicit in prose.

### 2.1 Per-intent mapping table

Columns: **saliency_focus** = which hierarchy driver the composition should lean on; **valence** /
**arousal** = affect targets (imported from affect literature, *directional only*); **memorability
cues** = properties associated with recall (distinct focal subject, unusual-but-coherent scene).

| Intent | Conversion goal | saliency_focus (NEvo driver) | valence | arousal | memorability cues |
|---|---|---|---|---|---|
| `peer_proof` | Trust → click CTA | **social configuration** (people oriented together, faceless) + matched scene | warm-positive | low–mid (calm) | one distinct workspace focal point; industry-native detail |
| `authority` | B2B hire decision | **body presence + scene gravitas** (observation/scrutiny), no faces | neutral-serious | mid | single stage-like focal scene; deliberate depth |
| `aspiration` | Individual apply | **single body/silhouette + implied motion** (mid-action at terminal) | positive | mid–high | lone hero silhouette, strong directional light |
| `roi_clarity` | HR/L&D buy-in | **social/joint-action** (champions returning, working together) | positive | low–mid | before/after arc as one readable composition |
| `loss_avoidance` | Urgency → act | **contrast/low-level split** (dim stall vs warm resolve) | mixed→resolving | mid–high | high-contrast split as the distinct hook |
| `retarget_warm` | Post-engager click | **familiar focal motif** (continuation) | warm-positive | low | consistent brand-gold motif = recognition cue |
| `message_match` | Ad click-through | **echo of ad's dominant driver** (continuity) | matches ad | matches ad | visual rhyme with the ad = recognition |

**Why this ordering is defensible:** it collapses to NEvo's replicated hierarchy — the highest-value
intents (`peer_proof`, `roi_clarity`) lean on **social configuration**, which NEvo shows is a
distinct high-level driver (pSTS); `aspiration`/`authority` lean on **body presence + implied
motion** (EBA/MT); `loss_avoidance` deliberately uses **low-level contrast** as an attention hook.

### 2.2 Candidate YAML shape (NOT implemented — proposal only)

Adds one optional `neuro:` block per intent. It is **prompt-assembly hinting**, not a new signal
and not per-visitor. Fields are enums so they stay inspectable on `/dev`:

```yaml
intents:
  - id: peer_proof
    conversion_goal: "Trust → click CTA"
    # ...existing fields unchanged...
    neuro:                         # OPTIONAL, additive, prompt-hint only
      saliency_focus: social       # social | body | motion | scene | texture | face(=disallowed, see §3)
      valence: warm_positive       # warm_positive | neutral | serious | mixed
      arousal: low_mid             # low | low_mid | mid | mid_high
      memorability_cues:
        - "single distinct focal subject"
        - "industry-native environment detail"
      evidence: "NEvo social-configuration driver (pSTS r~0.73); one-dominant-driver principle"
```

**How it would feed prompt assembly** (candidate, for `assemble_full_prompt` /
`assemble_base_prompt` in `image_intents.py`): append a short, human-readable clause such as
`"Attention structure: lead with {saliency_focus}; affective tone {valence}, energy {arousal};
reinforce recall via {memorability_cues}."` The `evidence` string is the important part — it lands
verbatim on the `/dev/image-decisions` receipt so every neuro hint is sourced, not asserted.

**Guardrail interaction:** `saliency_focus: face` must be **rejected at load time** — it collides
with the global `NO faces of real people` guardrail. `social`/`body` mean *faceless silhouettes and
configuration*, which is what our intents already do. The `neuro:` block changes **composition
guidance only**; it introduces **no new visitor signal, no new personalization layer, and nothing
that touches the `_hold` / tier-gate machinery.**

### 2.3 An optional offline scorer (the only place a NEvo-style loop belongs)

NEvo's real leverage is the **scorer + bounded search**. The on-brand, deployable analogue is an
**offline QA gate**, never a live neuro-loop:

- **Saliency QA gate** on the *composited* hero (backdrop + headline + CTA): run a public
  saliency model and assert the **headline/CTA zone is the attention peak, not the backdrop**. This
  objectively enforces our existing "image supports, does not compete with, the headline" rule.
- **Predicted-engagement score in the receipt** (CLIP-feature proxy → saliency-concentration,
  face/body presence): a **logged provenance number**, not a targeting input.
- **Offline base-image pre-optimization** in `scripts/pregen_segment_images`: pick among a few
  candidates per **non-personal segment base** using the scorer, bounded by `must_include` /
  `must_avoid`, **human-approved before caching.** Never per-visitor, never live.

---

## 3. What we should NOT do (the creepiness / hold line)

This is a **provenance project — the honesty is the product.** Neuro-flavored optimization crosses
the hold line the moment it becomes covert or per-person. Concretely:

- **NO live EEG/fMRI or any per-visitor biometric loop.** Infeasible on the web, requires hardware +
  consent, and directly violates our `NO surveillance, creepy, or behavioral-tracking imagery`
  guardrail. This is Tier-C "do not do."
- **NO per-visitor neuro-targeting.** The `neuro:` block must stay **per-intent and static**. It must
  never key off a specific person, their inferred emotional state, demographics, or `_hold` facts.
  Wiring affect targeting to an individual is the exact line this project exists to police.
- **NO faces of real/identifiable people**, unchanged. NEvo's strongest driver is faces — that is
  precisely the driver we **decline** to use, and the decisioning page should say so and *why*.
- **NO "maximize memorability" against a commercial black box.** The leading memorability model
  (ResMem) is **non-profit-licensed and its authors explicitly oppose advertising use**; memorable ≠
  persuasive besides. Adopt the *concept* (which features aid recall), not any prohibited library.
- **NO unbounded search.** Optimizing hard against any single scorer exploits its artifacts
  (NEvo's own warning) — a saliency-maxed image is often an ugly high-contrast mess. Any offline
  search stays inside brand `must_include`/`must_avoid` + human review.

### 3.1 How to disclose it on `/dev/image-decisions`

The decisioning page (`pipeline/personalization/gauntlet_image_decisions.py` →
`app/templates/gauntlet_image_decisions.html`, served at `/dev/image-decisions`) already narrates
"what the visitor feels" and "why it works" per intent. Recommended additions (research note, not a
code change here):

1. **A "neuroscience basis" line per intent** — surface the `neuro.evidence` string next to the
   existing `_WHY_IT_WORKS` copy, so each visual choice is sourced to the feature hierarchy.
2. **A standing "What we deliberately do NOT do" panel** — list the four refusals above (no live
   neuro, no per-visitor affect targeting, no faces, no commercial memorability-maxing). This turns
   the ethical line into a *visible product feature*, consistent with the say/allude/hold spine.
3. **Label any predicted-engagement number as a QA heuristic**, with the honest caveats:
   predicted ≠ actual, attention ≠ conversion, encoder bias is real.

---

## 4. Recommended next steps

**Implementable now (low risk, on-brand, still just proposals — nothing built in this memo):**

1. Add the optional per-intent `neuro:` block to `rules/_image_template.yaml` +
   `rules/gauntlet_image.yaml` as **documentation/prompt-hint fields**, with load-time rejection of
   `saliency_focus: face`. Pure additive; deterministic routing unchanged.
2. Surface `neuro.evidence` on `/dev/image-decisions` and add the "what we don't do" panel (§3.1).
3. Add a **saliency QA gate** on composited heroes as an offline check in QA/CI — assert the
   headline zone wins attention. Highest value-to-risk ratio of anything here.

**Research-only (validate before considering):**

4. Prototype a **Tier-B predicted-engagement proxy** (CLIP features → saliency-concentration /
   face-body presence) as an *offline* receipt annotation; measure whether its ranking correlates
   with anything we care about before trusting it.
5. Explore **offline evolutionary/bandit pre-selection** of segment-base images (NEvo architecture,
   minus the brain), human-approved before caching.
6. Watch for a **commercially-licensable** memorability/affect scorer; do not adopt ResMem.

**Explicitly out of scope / rejected:** live EEG/fMRI, per-visitor neuroadaptation, face-driven
heroes, commercial memorability-maxing (§3).

---

## 5. Verdict — "can we match our goals to brain stimulation?"

**Partly, and only in the honest direction.** We can ground our visual choices in NEvo's
*replicated feature hierarchy* (faces/bodies/motion/social/scene/texture) and borrow its
*architecture* (structured genes + offline predicted-response scorer + bounded search) as an
**offline QA gate**. We **cannot** "stimulate brains" per visitor, and NEvo says nothing about
persuasion or conversion — so no image can be claimed to convert at a rate on neuroscience grounds.
The safe, on-brand win is: make the vision-science basis for each intent **explicit and disclosed**,
add an objective saliency check, and publish the neuro-targeting refusals as a product feature.

---

## 6. Sources

- **NEvo project site** — https://nevo-project.epfl.ch/
- **NEvo preprint** — arXiv 2607.02317, Tang, Salehi, Zhou, Zamir, Isik, Schrimpf,
  *"NEvo: Neural-Guided Evolutionary Video Synthesis for Dynamic Visual Selectivity."*
- **NEvo pipeline / model card** — https://huggingface.co/epfl-neuroai/NEvo (V-JEPA 2 encoder,
  SDXL-Turbo + LTX-Video, fsaverage5 ROI masks, genetic-search defaults; research-use / hypotheses-
  to-validate framing).
- **EPFL NeuroAI Lab** — https://www.epfl.ch/labs/schrimpflab/ (Martin Schrimpf; Brain-Score lineage).
- Foundational selectivity replicated by NEvo: Kanwisher, McDermott & Chun (1997, FFA); Epstein,
  Harris, Stanley & Kanwisher (1999, PPA); Pitcher & Ungerleider (2021, third/social visual pathway,
  *Trends in Cognitive Sciences*); McMahon, Bonner & Isik (2023, lateral social-action hierarchy,
  *Current Biology*).
- Companion dossier (this repo): [`nevo-neuroadaptive-imaging-research.md`](nevo-neuroadaptive-imaging-research.md)
  — MindPilot EEG closed-loop work, ResMem license issue, saliency/affect predictor landscape.
