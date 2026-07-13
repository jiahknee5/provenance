# NEvo (EPFL) — brain-guided image/video generation, and its applicability to our image pipeline

> Research run 2026-07-09 for the `provenance` marketing-personalization demo. Part 1 is a sourced
> write-up of the EPFL **NEvo** project. Part 2 maps it — rigorously and skeptically — onto our hero
> image pipeline (`pipeline/personalization/image_gen.py`, `image_intents.py`, `rules/*_image.yaml`).
> Inline URLs throughout. Where the public material is thin, "what NEvo demonstrably does" is kept
> separate from "reasonable inference." **No code was changed; this is research + recommendation only.**

---

## Part 1 — What NEvo is

### 1.0 Name correction up front

The site at [nevo-project.epfl.ch](https://nevo-project.epfl.ch/) is **"NEvo — Neural-Guided
Evolutionary Video Synthesis"** (styled *NEvo*, not "NEVO", and not an acronym for a longer phrase).
The user's brief guessed **Pascal Frossard / LTS4**; that is **wrong**. NEvo comes from the **EPFL
NeuroAI Lab (PI Martin Schrimpf)**, with the [Swiss AI Center / Visual Intelligence and Learning Lab
(Amir Zamir)](https://vilab.epfl.ch/) and a Johns Hopkins group (Leyla Isik). Recording this so the
mapping below is grounded in the actual method, not the guessed one.

### 1.1 One-paragraph summary (demonstrable)

**NEvo** is a research framework that automatically **synthesizes short video (and image) stimuli
predicted to maximally activate a chosen region of the human visual cortex**. It is a product of the
**EPFL NeuroAI Lab**; the paper (*NEvo: Neural-Guided Evolutionary Video Synthesis for Dynamic Visual
Selectivity*) is authored by **Yingtian Tang, Sogand Salehi (EPFL), Ming Zhou (Johns Hopkins), Amir
Zamir (EPFL), Leyla Isik (Johns Hopkins), and Martin Schrimpf (EPFL)**
([arXiv 2607.02317](https://arxiv.org/html/2607.02317)). It ships as a self-contained Hugging Face
custom Diffusers pipeline, [`epfl-neuroai/NEvo`](https://huggingface.co/epfl-neuroai/NEvo). The goal is
scientific, not commercial: use an AI "digital twin" of the visual brain to *discover* what each cortical
region prefers to see — and, along the way, to generate **testable hypotheses for in-vivo neuroimaging
experiments** and, longer-term, for **targeted clinical interventions** (visual prostheses). Timeframe:
the preprint is dated **2026** (arXiv ID 2607 → July 2026); it builds on the lab's earlier static-image
and prosthetics work presented at **ICLR** (see §1.5). Funding is not stated on the public page; EPFL
NeuroAI is an EPFL IC/SV lab and part of the [Swiss AI initiative](https://www.swiss-ai.org/) ecosystem
(inference; not confirmed on the NEvo page itself).

### 1.2 The core scientific method — the actual pipeline (demonstrable)

The user asked whether NEvo (a) models neural responses to visual stimuli from brain recordings, then
(b) optimizes/generates images to maximally drive a targeted neural response. **Yes to both — with the
critical caveat that the "brain" driving the loop is a *model* (an encoding network), not a live brain.**
The pipeline (from the [paper §3](https://arxiv.org/html/2607.02317) and the
[HF model card](https://huggingface.co/epfl-neuroai/NEvo)):

```
target ROI r  (e.g. FFA, PPA, EBA, MT, V3A, pSTS — or arbitrary voxel set / fMRI vector)
      │
      ▼
structured PROMPT SPACE P  = Cartesian product of "genes":
      appearance genes (subject, scene, texture, lighting, mood, …)
      motion  genes (motion profile, temporal rhythm, camera motion, event/interaction type)
      │
      ▼
GENERATOR G:  text→image  = stabilityai/sdxl-turbo
              image→video = Lightricks/LTX-Video (distilled)   → a 2-second clip x = G(p)
      │
      ▼
BRAIN ENCODING MODEL  S_v  ("digital twin"):
      V-JEPA 2 video features (multi-block, space/time-averaged)
      → voxel-wise ridge regression fit to fMRI  → predicted response per voxel v
      ROI score  S_r(x) = mean over voxels in r of S_v(x)
      │
      ▼
EVOLUTIONARY (genetic) SEARCH over prompts P:
      population N=20; score each clip with S_r; keep top P_e=0.3 as parents;
      crossover P_c=0.5 (swap gene-prefixes); mutation P_m=0.2 (resample attributes);
      repeat for generations → predicted activation climbs
      │
      ▼
output: ranked synthetic clips predicted to best drive ROI r
```

Key specifics worth capturing:

- **Modality: fMRI.** The encoding model is trained on two video-fMRI datasets — **BOLDMoments**
  ([Lahner et al.](https://www.nature.com/articles/s41467-024-50310-3)) and a **social-interaction
  fMRI dataset** (Isik lab) — both projected onto the **`fsaverage5` cortical surface (20,484
  vertices)**, a *group-average* surface space, not a single subject's raw scanner space
  ([paper §3.3](https://arxiv.org/html/2607.02317); [HF card](https://huggingface.co/epfl-neuroai/NEvo)).
  This is an important nuance vs. the classic "subject-specific" framing — see §1.4.
- **Generative backbone:** frozen off-the-shelf diffusion models (SDXL-Turbo for stills, LTX-Video for
  motion). NEvo itself is the *search orchestrator*, not a new generator.
- **Search = evolutionary, not gradient.** They explicitly compare against the gradient-based
  **BrainDiVE** ([CMU BrainDiVE](https://www.cs.cmu.edu/~afluo/BrainDiVE/)) and find gradient guidance
  **fails** in the dynamic video setting, while genetic search is robust
  ([paper §4.3, Fig 4E/F](https://arxiv.org/html/2607.02317)). This matters for us (§2.4): the
  transferable trick is **generate-a-population → score → select**, which needs no differentiable path.
- **Two-stage search for efficiency:** first optimize a still image (≈400 eval budget), freeze the
  best "anchor," then optimize motion (≈200 evals). Static content and motion are optimized largely
  independently.
- **Open-loop / in-silico.** The reward is the encoding model's *prediction* — no human is in the loop
  while the search runs. **Closed-loop neuroimaging (testing whether the synthesized clips actually
  drive real human brains) is explicitly named as future work**, not something NEvo has done
  ([paper §5, "Future work… closed-loop neuroimaging"](https://arxiv.org/html/2607.02317)).

### 1.3 What it is used for / claims (demonstrable)

- **Map functional selectivity of visual cortex.** Synthesized clips recover textbook selectivities:
  face-like content for **FFA**, scenes for **PPA**, bodies for **EBA**, coherent motion for **MT/V3A**,
  social interaction for **pSTS/aSTS** ([site](https://nevo-project.epfl.ch/);
  [paper §4.1](https://arxiv.org/html/2607.02317)).
- **Beat the prior art on "how hard can you drive a region."** NEvo clips reach the **top ~99.8% of
  Moments-in-Time** natural-video responses and **~95.8% of handcrafted localizer** responses on
  average (predicted), and for every region the *moving* clip beats its own frozen first frame — i.e.
  these regions genuinely prefer dynamics ([paper §4.1–4.2](https://arxiv.org/html/2607.02317)).
- **Discover new structure.** A searchlight from V1 → aSTS shows a smooth gradient from low-level
  texture/motion toward **bodies, then coordinated interaction, then face-to-face social contact** — a
  finer-grained map of the "lateral (social) stream" than prior ROI-based work
  ([paper §4.4](https://arxiv.org/html/2607.02317)).
- **Controlled, hypothesis-driven stimuli.** Starting from an abstract anchor (two stacked plasticine
  discs) and optimizing only motion, pSTS optimization conjures face-like interacting characters while
  MT optimization yields pure motion — dissociating each region's preferred feature
  ([paper §4.5, Fig 6](https://arxiv.org/html/2607.02317)).
- **Clinical / vision-restoration angle (inference, but grounded).** The same lab's related line of
  work uses topographic neural networks to predict *where to stimulate* higher visual cortex to evoke
  perception of faces/objects (not just phosphenes), tested by Dutch collaborators in sighted-monkey
  trials and presented at ICLR — "AI brings object-level vision prosthetics closer to reality"
  ([EPFL news](https://actu.epfl.ch/news/ai-brings-object-level-vision-prosthetics-closer-t/)). NEvo's
  own paper frames the clinical use as *future* ("designing targeted clinical interventions"), so treat
  the prosthetics angle as **adjacent lab context, not a NEvo deliverable**.

### 1.4 Limits and caveats (demonstrable, from the paper's own Limitations)

- **It optimizes against a *model of the brain*, not a brain.** Synthesized stimuli "may reflect both
  neural selectivity and model bias"; the paper says in-vivo validation "is therefore necessary"
  ([§5 Limitations](https://arxiv.org/html/2607.02317)). The outputs are **hypotheses**, not verified
  neural controls. The HF card repeats this: "Research use… they are hypotheses… use held-out
  [validation]."
- **Group-space encoding, trained on two datasets.** The bundled encoder lives on the `fsaverage5`
  group surface. So the common "subject-specific encoding model of one measured individual" description
  is only *partly* right for NEvo-as-shipped: it's a model fit to specific fMRI datasets, in a shared
  surface space. (Subject-specific encoders are the norm in the broader field, e.g. BrainDiVE / NSD.)
- **Targets low/mid/high visual cortex, vision only.** No audio; regions like aSTS that depend on
  speech/audiovisual cues are under-served ([§5](https://arxiv.org/html/2607.02317)).
- **Structured prompt space is a constraint.** Interpretable "genes" improve control but "may omit
  relevant visual dimensions not captured by the schema."
- **Research artifact.** HF card: "Research use." Broader-impact note flags risk of "amplifying biases
  from framework components, including video generators and encoding models."
- **Needs neural data to exist at all.** The entire method is downstream of fMRI datasets used to fit
  the encoder. Without brain recordings there is no "twin," and without a twin there is no reward.

### 1.5 Sources

- Project site: [nevo-project.epfl.ch](https://nevo-project.epfl.ch/)
- Paper: [arXiv 2607.02317 (HTML)](https://arxiv.org/html/2607.02317) ·
  [v1](https://arxiv.org/html/2607.02317v1)
- Code/model: [Hugging Face `epfl-neuroai/NEvo`](https://huggingface.co/epfl-neuroai/NEvo)
- Lab: [EPFL NeuroAI Lab (Martin Schrimpf)](https://www.epfl.ch/labs/neuroai/) ·
  [VILAB (Amir Zamir)](https://vilab.epfl.ch/)
- Related lab prosthetics work: [EPFL news — object-level vision prosthetics](https://actu.epfl.ch/news/ai-brings-object-level-vision-prosthetics-closer-t/)
- Prior art referenced for contrast: [BrainDiVE (CMU)](https://www.cs.cmu.edu/~afluo/BrainDiVE/) ·
  V-JEPA 2 ([arXiv 2506.09985](https://arxiv.org/abs/2506.09985))

---

## Part 2 — Applicability to this project

The user's real question: *"Can we match our goals to brain stimulation and generate the appropriate
images?"* Short answer: **No — not literally, and we should not claim we can.** But the *structure* of
NEvo — optimize a stimulus toward a target response using a proxy scorer — is transferable, and there is
a genuinely useful, honest version we could build. Details below.

### 2.1 How our pipeline works today (grounding the mapping)

From `pipeline/personalization/image_gen.py` + `image_intents.py` + `rules/{planet,gauntlet}_image.yaml`:

- **Signals in:** deterministic, non-PII context from `build_image_ctx()` — channel, ad variant,
  audience route, industry (reverse-IP, tier-gated), coarse region, top objections, archetype, tier.
- **Intent selection:** `select_image_intent()` runs a **deterministic YAML rule engine** (no LLM,
  no learning) to pick a primary/secondary *intent* (e.g. Planet's `regional_truth`, `change_proof`,
  `mission_authority`; Gauntlet's `peer_proof`, `loss_avoidance`, `authority`).
- **Prompt assembly:** each intent carries a `composition_template`, `visual_metaphor`, `mood`,
  `sales_technique`, and an explicit `conversion_goal`. Guardrails strip hold-tier facts and enforce a
  `must_avoid` list (no faces, no logos, no text, no PII, no surveillance; Planet adds region-scale-only,
  no crosshairs).
- **Generation + cache:** `get_hero_image()` calls a **single** text-to-image API (OpenAI-compatible or
  Gemini `generateContent`), then writes a **two-tier deterministic disk cache** (segment "base" key +
  personalization "delta" key) with a full provenance receipt. Fallbacks: generated → curated gallery →
  CSS gradient. **`n=1` — one image per prompt, no scoring, no re-ranking.**

So today we generate **one** marketing hero image from **segment/intent/location** signals and cache it.
There is no objective function on the *output image* beyond "the prompt was assembled correctly and
passed guardrails."

### 2.2 The honest gap (say it plainly)

| | NEvo | Our pipeline |
|---|---|---|
| Target of optimization | a **measured brain**'s ROI activation (fMRI-fit encoding model) | a **marketing goal** (click/trust/comprehension) |
| Reward signal | a differentiable/queryable **brain "twin"** | **nothing** on the output image today |
| Loop | generate → **score** → **select/evolve** (100s of evals) | generate **once** (`n=1`), cache |
| Data required | video-fMRI datasets (BOLDMoments + social) | none beyond web signals |
| Backbone | SDXL-Turbo + LTX-Video + V-JEPA2 encoder | one text→image API |

**We have no brain data, no neural encoding model, and no neural reward.** Literal NEvo — closed-loop (or
even NEvo's open-loop-against-a-brain-twin) neural optimization of a stimulus — is **not applicable**.
There is no honest path from "reverse-IP says this visitor is in energy" to "this image will make their
fusiform face area light up." Claiming otherwise in a demo **whose entire thesis is provenance and
honesty** would be an integrity failure, not a feature.

### 2.3 What *is* transferable — in spirit, not in mechanism

NEvo's reusable idea is architectural: **define a target response, build a cheap proxy scorer for it,
then generate-and-select against that proxy.** Swap "brain ROI activation" for "marketing objective,"
and "fMRI encoding model" for "off-the-shelf vision-science proxies." Concretely:

- **The "response" becomes a marketing goal**, per intent: *attention/salience*, *trust/credibility*,
  *comprehension of change-over-time*, *urgency-without-fear* (already the language of our
  `conversion_goal` and `mood` fields, and of the Planet `change_proof` guardrail
  "urgent but dignified — the window is open, not closing in panic").
- **The proxy scorer becomes population-level vision science, not an individual brain:**
  - **Saliency / attention prediction** — e.g. [DeepGaze IIE](https://github.com/matthias-k/DeepGaze)
    (state-of-the-art free-viewing saliency), classic Itti-Koch, or spectral-residual saliency. Score
    *where the eye goes first* and whether that coincides with the headline/CTA zone (our templates
    already reserve an "empty upper third for headline overlay" — a saliency map can verify the hero
    focal point doesn't fight it).
  - **Visual clutter / complexity** — feature-congestion or subband-entropy clutter metrics; lower
    clutter ≈ higher "processing fluency," which our design principles already invoke.
  - **Color contrast / legibility** — WCAG-style luminance contrast in the headline zone; simple,
    deterministic, guardrail-friendly.
  - **Affect / valence priors** — population psych priors (warm vs cool palette, threat vs safety
    cues, center bias, face/gaze cueing, motion/change salience). Encode as **priors baked into the
    scorer**, not as claims about any person. This is exactly where NEvo-style "known selectivities"
    map onto *audience-agnostic* human-vision regularities.
  - **CLIP / VLM alignment** — score how well the generated image matches the *intended* structured
    prompt (composition, metaphor, mood) — a cheap "did we get what the intent asked for" check.
- **The real closed loop is engagement, not neurons.** If we want an actual feedback loop, it's **A/B
  test / click-through / scroll-depth** on the deployed variants — the honest analogue of NEvo's
  reward. That's the only "measured response" we can legitimately optimize against, and it's
  population-level and consented-analytics-based, not neural.

**Framed as a design:** `goal per intent → measurable proxy objective(s) → generate best-of-N →
rank by a saliency/affect/alignment scorer → existing two-tier cache`. This is NEvo's
generate→score→select skeleton, with a defensible proxy in the reward slot.

### 2.4 Concrete slot-in to the existing pipeline (proposal only — not implemented)

1. **Per-intent `objective` field in the YAML.** Add an optional key to each intent in
   `rules/planet_image.yaml` / `rules/gauntlet_image.yaml`, e.g.:
   ```yaml
   - id: regional_truth
     objective: [attention, trust]          # weights an image scorer
   - id: change_proof
     objective: [change_legibility, attention]
   ```
   This is purely additive and stays deterministic; absent the field, behavior is unchanged.

2. **Best-of-N + scorer step in `image_gen.py`.** Where we call the API with `n=1`, optionally request
   `N` candidates (or loop `N` prompt-mutations of the structured prompt — the *evolutionary* flavor),
   then rank them with a `score_image(candidate, objective)` function that combines the §2.3 proxies
   into a weighted score per the intent's `objective`. Cache the winner under the *same* two-tier key,
   and **log every candidate's score in the provenance receipt** (this is very on-brand for a
   provenance demo — the receipt shows "we generated 4, here's why #3 won").
   - NEvo lesson: use **selection over a population**, not gradients — our scorers (saliency maps, CLIP
     sims) are non-differentiable through a hosted API anyway, so best-of-N / light mutation is the
     right mechanism, exactly as NEvo found genetic search beat gradient guidance.

3. **Off-the-shelf scorers, zero brain data.** DeepGaze / spectral-residual saliency, a clutter metric,
   WCAG contrast in the headline region, and an open CLIP model for prompt-alignment. All run locally or
   via a small model; none require any neural recording or personal data.

4. **Cost / latency / guardrails.**
   - Cost/latency: best-of-N multiplies generation cost by N and adds scorer time. Mitigation: our
     **two-tier cache already amortizes this per segment** — best-of-N runs *once* per base/delta key,
     then every visitor hits the cached winner. Keep N small (3–4). Scoring a handful of images is
     cheap (sub-second for saliency/CLIP on GPU, a few seconds on CPU).
   - Guardrails: unchanged and still enforced — region-scale only, no surveillance, no faces/logos/text,
     truthful. The scorer selects *among already-guardrailed* candidates; it never relaxes a guardrail.
   - Provenance: the receipt gains `candidates_scored`, `objective`, `winning_score`, `scorer_models` —
     strengthening, not diluting, the honesty story.

### 2.5 Recommendation

- **Worth prototyping:** a **saliency/affect/alignment-guided best-of-N re-ranker** plus a **per-intent
  `objective`** grounded in *population-level vision-science priors* (attention, clutter, contrast,
  change-legibility). This is a real quality lift (better focal hierarchy, headline legibility,
  change-over-time readability) that fits our cache, our guardrails, and our provenance ethos — and it's
  the honest, defensible descendant of NEvo's generate→score→select loop.
- **Avoid entirely:** any framing of "brain stimulation," "neural optimization," "brain-aligned," or
  "activates your visual cortex." We have **no brain data**; such claims would be false and would
  directly contradict the demo's provenance thesis. Even NEvo's own outputs are *hypotheses about a
  model of the brain* pending in-vivo tests — a bar we cannot and should not pretend to clear.
- **Optional, later, honest closed loop:** wire the *real* reward — A/B engagement on deployed variants
  — back into intent/objective weights. That's the only "measured response" we can legitimately optimize.
- **Rough effort estimate (if greenlit):**
  - YAML `objective` field + plumbing through `build_structured_prompt` / receipts: **~0.5 day.**
  - Best-of-N generation loop + `score_image()` with 2–3 proxies (saliency + contrast + CLIP align):
    **~2–3 days** including tests and a `/dev` panel row showing the scored candidates.
  - Optional light "evolutionary" prompt-mutation instead of plain best-of-N: **+1 day.**
  - A/B engagement feedback loop: separate, larger effort (**~1 week+**), depends on analytics infra.
  - **MVP (per-intent objective + best-of-N re-ranker with saliency + contrast + CLIP alignment,
    logged in the receipt): ~3–4 days.**

### 2.6 TL;DR

- **NEvo** = EPFL NeuroAI Lab (Schrimpf et al.) framework that **evolves AI-generated video/images to
  maximally drive a target region of a *model* of the human visual cortex** (V-JEPA2→fMRI encoder as the
  reward, SDXL-Turbo + LTX-Video as the generator, genetic search as the optimizer). It's in-silico,
  fMRI-based, open-loop against a brain "twin," and its outputs are **hypotheses**, not verified neural
  controls. (Not Frossard/LTS4.)
- **Can we "match our goals to brain stimulation and generate the appropriate images"?** **No.** We have
  no brain data, no neural encoding model, and no neural reward, so literal neural optimization is out —
  and claiming it would break the demo's honesty premise.
- **The honest version we *can* build:** keep NEvo's generate→score→select *shape*, but put a
  **marketing-goal proxy** in the reward slot — saliency/attention, clutter, color-contrast, and
  prompt-alignment scorers plus population-level vision-science priors — as a **best-of-N re-ranker**
  driven by a new per-intent `objective` field, all inside the current guardrails and two-tier cache,
  with every candidate's score written to the provenance receipt. ~3–4 days for an MVP. Real closed loop
  = A/B engagement, not neurons.
