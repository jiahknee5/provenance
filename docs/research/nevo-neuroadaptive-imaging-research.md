# NEVO / Neuroadaptive Image Optimization — research dossier

> Source: primary read of the EPFL **NEvo** project (project site, arXiv preprint, Hugging Face
> pipeline) plus the closely-related **MindPilot** EEG paper and the off-the-shelf
> "predicted-response" model landscape (ResMem, EML-NET/saliency, affect predictors).
> Read date 2026-07-09. This feeds the hero-image personalization pipeline
> (`pipeline/personalization/image_intents.py`, `rules/*_image.yaml`,
> `*_image_decisions.py`). See [ACTION-IMAGE-PERSONALIZATION.md](../04-workflow/ACTION-IMAGE-PERSONALIZATION.md)
> and [copy-personalization-research.md](copy-personalization-research.md).
>
> **Discipline (same as the copy dossier):** treat the *mechanisms* as load-bearing and the
> *magnitudes* skeptically. NEvo's numbers are *predicted* neural activations under one encoder,
> not measured human responses — the authors say so explicitly. Everything below is a hypothesis
> generator for visual strategy, never a "this image will convert X%" claim.

---

## 0. TL;DR for the pipeline

- **NEVO is `NEvo` — "Neural-Guided Evolutionary Video Synthesis."** It is a *basic-neuroscience
  tool*, not a marketing tool: it evolves AI-generated video prompts to maximally drive a chosen
  region of the human visual cortex, scored by a "digital-twin" brain encoding model. It maps
  *which visual features a brain region cares about*, in silico.
- **The transferable idea is the architecture, not the brain claim.** NEvo = `structured prompt
  space (genes) → generator → predicted-response scorer → evolutionary search`. Our pipeline
  already has the first two pieces (YAML intents = genes, Gemini image API = generator). NEvo is a
  blueprint for the missing pieces: a **scorer** and a **search loop**.
- **The science it recovers is a feature hierarchy** (low-level texture/contrast → motion → bodies
  → faces → social interaction) that lines up cleanly with our existing intents (`peer_proof`,
  `authority`, `aspiration`) and tells us *which visual properties* plausibly drive attention and
  approach motivation.
- **Do NOT wire real EEG/fMRI or the actual brain-encoding model into a landing page.** That is
  neither feasible nor on-brand (surveillance guardrails). The usable, deployable analogue is
  **off-the-shelf image predictors** — memorability (ResMem), saliency (EML-NET-class), and
  aesthetic/affect scorers — used offline as a *ranking/QA gate*, not a live neuro-loop.
- **Ethics flag up front:** ResMem's authors explicitly **prohibit for-profit/marketing use** and
  worry about "unforgettable ads." Any predicted-response scoring we adopt must be documented on the
  `/dev` decisioning page as a *heuristic quality filter*, disclosed, and kept clear of the
  manipulation line. This is a provenance project — the honesty is the product.

---

## 1. What NEvo actually is

### 1.1 One-sentence definition
NEvo generates short (2-second) AI videos and iteratively evolves them to **maximally activate a
target brain region** (e.g. the fusiform face area), using a neural network "digital twin" of the
brain to predict activation as the search reward. It answers: *"What kind of video would make a
given part of your visual brain light up the most?"*

### 1.2 Who runs it
- **EPFL NeuroAI Lab** (`epfl-neuroai` on Hugging Face) — **Martin Schrimpf** (senior author;
  Brain-Score / brain-encoding-model lineage).
- **Amir Zamir** — EPFL Visual Intelligence & Learning Lab (computer vision / generative models).
- **Yingtian Tang, Sogand Salehi** (EPFL) — equal-contribution first authors.
- **Leyla Isik, Ming Zhou** (Johns Hopkins) — social-vision / lateral-stream expertise.
- Preprint: *"NEvo: Neural-Guided Evolutionary Video Synthesis for Dynamic Visual Selectivity"*
  (arXiv 2607.02317). Project: `nevo-project.epfl.ch`. Code/pipeline: `huggingface.co/epfl-neuroai/NEvo`.

> Note on a name collision: an unrelated EPFL post-doc ad (MIP:Lab, Dimitri Van De Ville, with the
> startup *Dandelion Science*) also describes "generative video linked to evoked neural dynamics."
> That is a *different* group. The project the task points to is the Schrimpf/Zamir/Isik `NEvo`.

### 1.3 Method (the part we actually reuse)
Four components in a loop (paper §3):

1. **Structured "gene" prompt space.** Every candidate is described by discrete genes across
   ~30 image categories (614 options) + ~11 video-motion categories (163 options). Genes are grouped
   by visual-hierarchy level:
   - *Low-level:* `Pattern`, `SpatialFrequency`, `EdgeDensity`, `Surface`, `Color`, `Texture`.
   - *Mid/high:* `ObjectForm`, `BodyContent`, `BodyAction`, `FaceContent`, `FaceViewpoint`,
     `SceneCategory`, `SceneGeometry`.
   - *Social:* `SocialDynamics`, `SocialCue`, `IntentionSignal`, `AgentNumber`.
   - *Motion (video stage):* `MotionStrength`, `TemporalRhythm`, `PrimaryAction`, `Interaction`,
     `EventStructure`, `CameraMotion`.
   - *Quality anchors:* `Mood`, `Style`, `RenderType`, `Lighting`, `Framing` — these don't map to a
     known brain preference; they exist to keep the generator coherent and give search room to
     explore. **This is exactly our `mood` / `color_rules` / composition fields.**
2. **Generator `G`.** SDXL-Turbo (single-step, 512×512) for the image stage; LTX-Video for the
   2-second animation stage. (We use Gemini image gen — same slot.)
3. **Scorer `S` — the "digital twin".** V-JEPA 2 video features → voxel-wise ridge regression to
   fMRI, trained on public video-fMRI datasets (BOLDMoments + a social-interaction set). Predicts
   per-voxel response; ROI score = mean over the region's voxels. Multi-layer beats CLIP-last-layer;
   video beats a single frame.
4. **Evolutionary search.** Population 20, keep top 30% as elites, crossover 0.5, per-gene mutation
   0.2. Two stages for efficiency: first find the strongest **still image** (~400 evals), then fix
   it and search **motion** (~200 evals). Genetic search beat random search and hill-climbing;
   gradient-based synthesis (BrainDiVE) *failed* in the video setting — **black-box evolutionary
   search over discrete prompt genes was the robust choice.** (Directly relevant: our prompt space
   is also discrete/structured, so evolutionary/bandit search fits and gradients don't.)

### 1.4 Key results
- Synthesized clips drove predicted activation **above** hand-crafted localizer videos and the best
  natural videos (top ~96–99.8% of reference distributions).
- Recovered known selectivity per region: **faces → FFA, places/scenes → PPA, bodies → EBA, motion
  → MT, patterns/texture → V1/V3A, social interaction → pSTS/aSTS.**
- Sliding a "searchlight" from early to higher visual cortex produced a **smooth gradient: simple
  high-contrast patterns → motion → bodies → dyadic physical interaction → face-to-face social
  contact.** Even starting from abstract shapes, optimizing for the social region *conjured
  face-like interacting characters*; optimizing for the motion region produced pure motion.
- **Limitation stated by the authors:** results reflect *both* neural selectivity *and* encoder
  bias; they are **predictions to validate in vivo, not ground truth.** Optimizing hard against one
  encoder can exploit its artifacts.

### 1.5 Sister work — MindPilot (EEG, closed-loop, includes *affect*)
`MindPilot` (arXiv 2602.10552, SUSTech/U-Delaware) is the closest thing to "neuroadaptive marketing"
in the literature and worth knowing because it closes the loop the way a naive stakeholder might
imagine we could:
- Treats the brain/EEG as a **black-box** `g`; optimizes images so the *evoked* EEG feature matches
  a target (semantic CLIP-space target, spectral target, or **self-reported emotional valence**).
- Uses an **image→EEG proxy model** so it doesn't need live EEG every step (even AlexNet/ResNet50
  proxies worked), then validates on 10 real human subjects.
- **Emotion-regulation result:** steering toward positive valence moved mean self-rated valence
  0.45 → 0.60 over 10 iterations, and the proxy's predicted reward correlated with human ratings
  (R ≈ 0.71). Fine-grained "mental matching" was only moderate — the honest sim-to-real gap.
- Takeaway for us: **affect is steerable by image content and a *predicted* affect score tracks real
  ratings well enough to be a useful offline ranking signal** — but this required lab EEG + consent
  + per-subject noise. It validates the *direction* (predicted-response scoring works) while making
  clear the *live-neuro* version is a research rig, not a web deployment.

---

## 2. The transferable science

### 2.1 Which visual properties drive which response (from NEvo's property–activation table)
NEvo annotated 1,052 videos on a 0–10 scale (22 perceptual/social properties, high annotation
reliability) and correlated each with predicted regional activation. The robust, direction-level
findings that transfer to *what makes a hero image work*:

| Visual property | Drives (region) | Marketing read-across |
|---|---|---|
| **Face presence** | FFA 0.88, pSTS 0.82, aSTS 0.76 | Faces are the single strongest attention/again-look driver. Human faces recruit dedicated cortex. |
| **Body presence** | MT 0.87, EBA 0.84, pSTS 0.87 | Human figures (even faceless silhouettes) strongly engage the visual system → our "silhouette, no face" intents are well-founded. |
| **Biological / coordinated motion** | MT 0.84, EBA 0.84, pSTS 0.75 | Implied motion and "aliveness" are potent — for static heroes, *implied* motion (frozen mid-action) is the lever. |
| **Joint action / facingness / synchrony** | pSTS 0.69–0.73 | *Social interaction* (two agents oriented to each other, acting together) is a distinct, high-level driver → maps to `peer_proof`, `roi_clarity` (people working together). |
| **Spatial complexity / texture richness** | V1 0.93 / 0.71 | Dense high-contrast texture drives *early* attention capture but not higher-order meaning — useful for a first-glance grab, risky if it competes with the headline. |
| **Spatial expanse / navigation / curvature** | PPA 0.78 / 0.67 / (neg for angular) | Open scenes and "walk-into-it" perspective drive scene cortex → the `{environment}` backdrop lever (our `industry_env`). Curvature preference is a known aesthetic pull. |

**The clean, defensible synthesis** (consistent with mainstream vision science, not just NEvo):
1. **A single clear focal point wins.** NEvo's whole method presumes one dominant driver per image;
   our pipeline already encodes "single focal point — processing fluency." Reinforced.
2. **Faces > bodies > motion > scene/texture** as an attention/engagement hierarchy. Text is a
   *distractor* to the visual system for a backdrop (our "NO text in image" guardrail is
   well-motivated — text competes for the same fixation budget the headline needs).
3. **Social configuration is its own high-level driver.** "Two people oriented toward each other,
   doing something together" is processed by dedicated machinery — this is the visual analogue of
   the copy dossier's *matched-peer social proof*.
4. **Depth / open perspective / gentle curvature** are low-risk aesthetic pulls for backdrops.
5. **High-frequency texture grabs the eye first but carries no meaning** — use as accent, never as
   the element that has to survive next to the headline.

### 2.2 Are "predicted brain response" models usable *for us*? (the core question)
Short answer: **yes as an offline ranking/QA signal, no as a live per-visitor neuro-loop.** Three
tiers, in order of deployability:

**Tier A — deployable now, off-the-shelf image predictors (recommended).**
- **Memorability — ResMem** (UChicago Brain Bridge Lab, `pip install resmem`, ResNet-based, 0–1
  score, Spearman ≈ 0.64 vs human memorability). **BLOCKER:** license is **non-profit only; authors
  explicitly prohibit for-profit/advertising use** and note that memorable ≠ persuasive. → Do **not**
  ship ResMem in a commercial pipeline. Use only for internal research/benchmarking, or find a
  commercially-licensed equivalent. Treat "memorability" as a property we *can* discuss, not a
  library we can bundle.
- **Saliency — EML-NET / SALICON-class models** (predict where eyes go; MIT300/CAT2000/SALICON
  benchmarks; permissive research code). Genuinely useful as a **QA gate**: run the *composited*
  hero (backdrop + headline + CTA) through a saliency map and verify the **headline/CTA is the
  attention peak, not the background**. This directly enforces our "image supports, does not compete
  with, the headline" principle — objectively.
- **Aesthetic / affect predictors** (LAION-aesthetic scorer; valence/arousal regressors; ad-saliency
  models). Directional only; usable as a soft tie-breaker.

**Tier B — feasible but heavier: build a proxy scorer (the MindPilot recipe minus the brain).**
Train/borrow an `image → property vector` model (CLIP features → ridge/regression heads for
saliency-concentration, face/body presence, valence). Score is *predicted*, cheap, deterministic,
loggable. This is the honest version of "digital twin" for our context: a **predicted-engagement
model**, explicitly labelled as such. No neural data, no per-user tracking.

**Tier C — do NOT do: live EEG/fMRI or per-visitor neuroadaptation.** Infeasible on the web,
requires consent + hardware, and collides head-on with our surveillance/PII guardrails and the whole
provenance ethos. Worth a paragraph on the decisioning page explaining *why we deliberately don't*.

### 2.3 Honest limits (put these on the decisioning page)
- Predicted ≠ actual. NEvo/MindPilot both stress the encoder-bias / sim-to-real gap.
- Optimizing hard against any single scorer **exploits its artifacts** (NEvo's explicit warning) —
  a saliency-maximized image can be an ugly high-contrast mess. Any search must be bounded by our
  brand `must_include`/`must_avoid` and human review, exactly as our guardrails already do.
- **Memorable/attention-grabbing ≠ converting.** ResMem's authors found memorability doesn't
  strongly change decisions; NEvo doesn't touch persuasion at all. Attention is necessary, not
  sufficient — copy still carries the argument.
- Ethics: the memorability-model authors refuse marketing use on principle. We should adopt the
  *science* (which features draw the eye) and the *architecture* (structured genes + scorer +
  search), disclose it, and stay far from covert optimization.

---

## 3. Mapping NEvo → our pipeline (concrete)

| NEvo component | Our current analogue | Gap / opportunity |
|---|---|---|
| Gene prompt space (614+163 discrete options, grouped by hierarchy level) | `rules/*_image.yaml` intents: `composition_template`, `visual_metaphor`, `mood`, `color_rules`, `{environment}`, `{ad_metaphor}`, `{objection_metaphor}` | Our "genes" are hand-written per intent. NEvo shows a **richer, orthogonal, hierarchy-tagged** attribute set. Could expand our template slots (focal-subject, implied-motion, social-configuration, depth) as explicit, swappable genes. |
| Generator `G` (SDXL/LTX) | Gemini image API (`image_gen.py`) | Same slot; no change needed. |
| Scorer `S` (brain digital twin) | **Missing** | Add a **Tier-A/B predicted-engagement scorer** (saliency-concentration on the headline zone + face/body presence + aesthetic), run **offline** on candidates. Log score on the `/dev` receipt as provenance. |
| Evolutionary search | Deterministic rule selection (no LLM in routing) | Keep routing deterministic for *which intent*. Optionally add an **offline** evolutionary/bandit loop that pre-optimizes the *base segment images* (Tier-1 cache) against the scorer, so the cached asset is the attention-validated one. Never a live per-visitor loop. |
| "One dominant driver per region" | "single focal point — processing fluency" | Already aligned; the science backs it. |
| Property→response table (faces/bodies/motion/social/texture) | Intent design principles | Use as an evidence base in `*_image_decisions.py` "why this image" copy — grounds each intent's visual choices in vision science. |

### 3.1 Suggested, guardrail-safe additions (if the parent wants to act)
1. **Saliency QA gate** on the *composited* hero: assert the headline/CTA region is the saliency
   peak; flag heroes where the backdrop out-competes the message. Cheap, objective, on-brand.
2. **Predicted-engagement score in the receipt** (Tier B, CLIP-feature proxy): a logged number, not
   a targeting signal — pure provenance/QA.
3. **Offline base-image pre-optimization** (`scripts/pregen_segment_images`): evolve/select among a
   few candidates per segment using the scorer, bounded by `must_include`/`must_avoid`, human-approved
   before caching. This is the *only* place a NEvo-style search belongs — offline, on non-personal
   segment bases, reviewed.
4. **Decisioning-page section**: explain the science (feature hierarchy), what we borrowed (structured
   genes + scorer + offline search), and — importantly — **what we refuse** (live neuro-loops,
   per-visitor biometric optimization, ResMem-style commercial memorability maxing).

---

## 4. Sources
- NEvo project site — `https://nevo-project.epfl.ch/`
- NEvo preprint — arXiv `2607.02317` (Tang, Salehi, Zhou, Zamir, Isik, Schrimpf).
- NEvo pipeline / model card — `https://huggingface.co/epfl-neuroai/NEvo`
  (V-JEPA2 encoder, SDXL-Turbo + LTX-Video, fsaverage5 ROI masks, genetic search defaults).
- MindPilot — arXiv `2602.10552` (EEG-guided closed-loop diffusion; emotion-regulation 0.45→0.60,
  proxy–human R≈0.71). Repo: `github.com/ncclab-sustech/MindPilot`.
- ResMem — Needell & Bainbridge (2022), `brainbridgelab.uchicago.edu/resmem` /
  `github.com/Brain-Bridge-Lab/resmem`. **Non-profit-only license; authors oppose marketing use.**
- EML-NET saliency — Jia & Bruce (2020), `github.com/SenJia/EML-NET-Saliency` (SALICON/MIT300/CAT2000).
- Saliency→emotion — Yaragoppa & Siddharth (2025), arXiv `2505.19178` (single vs multi salient
  region ↔ valence/arousal — directional only).
