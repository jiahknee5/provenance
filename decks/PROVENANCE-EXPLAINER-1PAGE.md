One-pager · plain English · no marketing knowledge needed · **⌘P → Save as PDF**

Capstone project · looking for teammates

# Provenance — the outbound AI that can't lie

An AI that writes a personal message to every customer — and is **physically unable to say anything it can't prove** from a trusted source.

Picture an AI writer with a **fact-checker bolted to its mouth**. Before any sentence leaves the building, a second system checks it against the source documents and blocks it if the proof isn't there. That second system is Provenance.

## 1. The problem (you don't need to know marketing)

Companies send outreach messages — sales emails, ads, follow-ups. AI can now write a **unique** message for every single person: millions of them, all different. Great… except **someone has to make sure each message is true and legal.**

- A human can check 100 messages. **Nobody can read 1,000,000.**

- Get a fact wrong in medicine, finance, or food and you get **sued or fined.**

- So today everyone picks a bad option: send **boring identical** messages (safe but ignored), or send **personal but unchecked** messages (effective but risky).

"Verification is the new bottleneck." The hard part of AI is no longer **writing** — it's **checking**. That's the gap we attack.

## 2. What it is & what it does

Provenance is a **system of record for claims** — the way a bank ledger is the record for money, this is the record for every factual statement your company makes.

- Every fact (*"saves about $10 per animal"*) becomes a tracked **claim** with a receipt: where it came from, whether it was verified, whether it's allowed, and how it performed.

- Before anything sends, the message is chopped into individual claims and each one must pass the check — **cited or killed.**

- It also **learns to write more persuasive messages over time** — but it's only ever allowed to pick from statements that already passed. So it gets better **without ever lying.**

## 3. Why it's interesting

- It takes on the **hottest open problem in AI** — verification at scale — end to end, not as a toy.

- **One genuinely novel bet:** tell an AI "get more replies" and it learns to **exaggerate** (called *reward-hacking*). Our fix is structural — it can only choose among **already-verified** statements, so it **literally cannot win by lying.**

- You build a **real, live thing** with real data. The demo is a magic trick: we hand the audience the controls, **try to make it lie — and watch it refuse.**

## 4. The technology

- LLM writes the messages and splits them into atomic claims.

- NLI + judge ensemble calibrated, answers one question: *does the source actually support this claim?* A single AI judge is biased & gameable; an ensemble isn't.

- router + referee cheap check first, expensive check only on close calls.

- contextual bandit a reinforcement-learning method that picks the winning message — constrained to verified options only.

- drift monitor a claim-dependency graph: change a source doc and every claim that leaned on it is re-checked.

- Assurance Lab adversarial traps that try to fool the checker — so we can *prove* it works.

## Want in?

- **Team of 3–4 · 2-week build · live showcase Mon Jun 29.**

- Looking for people who like any of: **ML / NLP, evaluation & verification, reinforcement learning,** or building clean systems.

- **Zero marketing knowledge required.** Making the messages is the easy part; making the AI *trustworthy* is the interesting part — that's your job.

- If **"an AI that's structurally incapable of lying"** sounds fun to build, you're exactly who we want.
