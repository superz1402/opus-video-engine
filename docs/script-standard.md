# Script Standard — opus-video-engine (v1, 2026-10-27)

**Purpose:** the scripting + narration standard every engine project is
written and gated against. It extends — does not replace — the Orb Theory
retention rubric (`retention-scripting.md`, ≥16/20, no zero dimensions) and
the Archivist character bible. Where this standard adds measurable checks,
they are **additional gate items**, scored at the same S2 stop.

**Provenance:** harvested from open-source practice — see the
scripting-narration research report (2026-10-27, held outside this repo)
for sources per rule. Key debts: but/therefore chaining & jagged-edge
rhythm (artemnovitckii/content-skills, MIT); hook scoring & formulas,
including the self-resolving-hook penalty (Jakeschincariol/
youtube-agent-skill, MIT); four-killers hook audit (content-skills
viral-hooks); earned-vs-hollow contrast test (content-skills
anti-ai-writing); pause/emphasis markup (remsky/Kokoro-FastAPI SSML map,
Apache-2.0). Concepts are adapted here in this engine's own words and
code; no upstream code is vendored.

**Status in this engine:** adopted by the owner on 2026-10-27 ("adopt it
for now" — provisional v1, subject to revision as productions prove or
disprove it). This document is LAW for the scripting stage: see AGENTS.md
stage P1.5 and hard rule 11. The mechanical subset of §5 is implemented
by `engine/script_gate.py` and runs in CI
(`.github/workflows/script-gate.yml`) on every script change — a gate
FAIL blocks P2 voice; the script is rewritten, not produced. The gate
script covers T3 (spoken-question count), T5 (opener/template proxies),
T6 (jagged edge), T9 (pivot count), T10 (delivery marks), T11 (slop
lint), the §1.1 self-resolving-hook heuristic, and the §4 pace sanity
estimate. T1, T2, T4, T7, T8 and T12 are scored at the gate by the
independent scorer — never the writer: **a self-scored script's recorded
rubric total caps at 15/20** (§5), so no self-scored script can certify
its own pass.

---

## 1. The hook — first 5 seconds, then the first 30

### 1.1 The first spoken line (≤5 s of audio, 9–24 words)

Must do all four jobs (a summary is not a hook):

1. **Confirm the promise** — the title/thumbnail's claim is acknowledged in
   sentence one. A hook that ignores its own title leaks at ~0:08.
2. **Open a gap the viewer cannot close** — an unanswered question, an
   impossible fact, or a contradiction *whose resolution is withheld*.
   **Self-resolving hooks are banned:** if the line contains "because",
   "which means", or its own answer, it is a summary. (Thesis statements —
   "It's a different body plan" — are summaries.)
3. **Prove the payoff exists** — a specific, checkable detail (a number, a
   named thing, a shown artifact) that signals the answer is real and
   coming.
4. **Could open no other video** — the noun-swap test from the existing
   rubric still applies.

### 1.2 Construction method (mandatory)

- Write **five** hook candidates, each from a **different formula family**
  (statistic / impossible / question / mistake / reveal / comparison /
  origin / direct-address — never five rewordings of one idea).
- Score all five with the five-property panel (specificity · address ·
  stakes · curiosity · brevity). Keep the top two; record both scores in
  the project. Ship the winner; archive the runner-up.
- Run the **four-killers audit** on the winner: DELAY (topic not in the
  first noun phrase), CONFUSION (two-pass parse), IRRELEVANCE (no viewer
  stake / no you-pivot), DISINTEREST (no A-vs-B gap). Any FLAG → rewrite.

### 1.3 The first 30 seconds

| Window | Job |
|---|---|
| 0:00–0:05 | Hook line (§1.1) over the strongest visual, already moving |
| 0:05–0:15 | **Escalate, don't explain** — a second, stranger fact or the cost of the first one. No topic summary, no "here's what we'll cover" |
| 0:15–0:30 | **Plant the episode loop** — one specific question, stated as a question, that the final third will pay. Say it as a question ("So who gives the orders?"), not as a topic ("next, the nervous system") |

Long-form: the loop is re-planted per chapter (existing long-form deltas
apply); Shorts: the loop and payoff live inside the runtime.

---

## 2. Scene grammar

### 2.1 But/therefore chaining (the spine rule)

Between every pair of scenes — and between beats inside a scene — the
connector must be **BUT** (complication) or **THEREFORE** (consequence).
"And then" (mere addition) is banned as a structural connector. Method:
at storyboard stage, write the chain literally under each scene heading:

```
S3 weapons ──THEREFORE──▶ S4 nerves (claws bought it a still victim;
                          now it needs the victim to *walk*)
S4 nerves ──BUT──▶ S5 breathing (a body run by committee still has
                          to breathe — and it does it without lungs)
```

If neither word fits between two scenes, one of them is catalogue filler:
reorder, merge, or cut it. **Catalogue order (anatomy order, chronology
order, list order) is a storyboard defect**, not a neutral choice.

### 2.2 Question ladders

- Each scene **answers the question the previous scene raised and raises
  the next one** — a ladder, not a list. The storyboard names, per scene:
  *question in → answer → question out*.
- Narration carries the ladder audibly: **≥1 genuine spoken question per
  scene** in explainer formats (long-form: ≥1 per chapter, plus the
  re-planted loops). A question the narration answers in the same breath
  doesn't count; the answer must cost at least one scene beat.
- Rhetorical-question spam is not a ladder: max 2 consecutive scenes may
  *open* with their question; vary placement (open / middle hinge / close).

### 2.3 Stakes escalation

- Scenes are ordered by **rising consequence**, not by topic completeness.
  Each scene's storyboard row states its stake in one line ("so-what"):
  what breaks, costs, or becomes possible because of this fact. A scene
  whose so-what is "it's interesting" is cut or merged.
- The most consequential scene sits at 60–80% of runtime (the existing
  centrepiece rule); the finale pays the master loop and *recontextualises*
  the hook fact — it never merely restates the thesis.
- **Agency rule:** the subject must *do* things. In narration, action
  verbs performed by the subject outnumber copulas (is/has) in every
  scene. Facts attach to behaviours in progress ("while it hunts…",
  "to reach the burrow it must…"), not to static diagrams.

### 2.4 Contrast discipline (earned vs hollow)

- The negative pivot ("not X — it's Y", the Archivist's dry pivot) is
  **rationed: ≤2 per episode, ≤1 per scene**, and each must pass the
  two-part test: (1) the Y half is concrete — an instance, number, or
  mechanism, not a category ("mindset", "a different plan" unadorned);
  (2) the following 30 s deliver it. Hollow pivots are rewritten as direct
  claims.
- Them/you (or A/B) comparison is a *device*, not a *structure*: max 2
  consecutive scenes may use the same comparison template; the third must
  change shape (scene, question, demonstration, verdict).

---

## 3. Sentence rhythm — written for the voice, not the page

TTS reads exactly the rhythm you write. Flat writing cannot be performed
into life.

1. **Jagged edge.** Draft narration one sentence per line. Read down the
   left edge: line lengths must visibly vary. Three consecutive sentences
   within ±2 words of each other = a flat stretch → rewrite.
2. **Length budget.** Median sentence 8–14 words. Hard caps: no sentence
   >20 words unless it is a *built* sentence (a deliberate escalating list
   whose clauses shorten); **≥2 fragments (≤4 words) per scene** placed as
   beats, not accidents. (Proof data point: our catalogue script's middle
   scenes settled into 22-word em-dash chains — the drone zone.)
3. **Breath points.** One idea per sentence; a sentence containing two
   em-dash insertions or a nested subordinate chain fails — split it.
   Commas are breaths; semicolons are half-beats; the TTS will find
   neither if the clause chain runs past ~14 words without one.
4. **No template rhythm.** If two adjacent scenes share an opener pattern
   (e.g., both start "Its… / It has…"), rewrite one opener — openers
   rotate: claim / question / fragment / number / object / action.
5. **Read-aloud test.** The draft is read aloud (human or TTS draft)
   before scoring. Any line the reader stumbles on, or that sounds like a
   speech instead of a person talking to one viewer, is rewritten.
   "Talk to one person" is the register check.

---

## 4. Narration delivery — markup the voice stage must honour

Scripts carry delivery markup; the voice stage (Edge production / Kokoro
local) is **required to implement it**, not strip it. A synth that reads a
scene as one flat paragraph at one speed fails this standard.

| Markup | Meaning | Voice-stage implementation |
|---|---|---|
| `[PAUSE]` | Full beat of silence, 0.6–0.9 s | Split synthesis at the mark; insert measured silence |
| `[PAUSE:short]` | Half-beat, 0.3 s | As above, shorter slot |
| `[ASIDE] … [/ASIDE]` | Character aside — drier, closer | Rate −4–6% relative, split chunk, delivered flat (never signalled as a joke) |
| `**word**` | Emphasis word | Separate chunk or rate −3% on the word's chunk; on Edge, SSML `<emphasis>` where supported |
| `[SLOW] … [/SLOW]` | Verdict / payoff lines | Rate −8–10% for the span (the sign-off's "slowed a half-beat", generalised) |
| `[[rate:+5%]]` | Local pace lift (energy beat) | Chunk-level rate override; whole-line only, never mid-word |

**Number handling (spoken forms, mandatory at S2):**

- Numbers are written **as they should be spoken** in the narration text
  ("a hundred and ninety-one", "ten to seven to four"); digits live in
  captions/on-screen text. (TTS digit rendering varies by engine; the
  script, not the synth, owns the choice.)
- Ranges spoken as "fifteen to a hundred and ninety-one pairs", never
  "15–191".
- Percentages, ratios, and chemical formulae carry a `say:` note in the
  script's lexicon block (existing lexicon practice, now mandatory for
  *every* number, not just names).
- A number used as a hook must be **escalated or paid**, not repeated:
  state it once at full weight; later mentions may shorten ("the hundred
  and ninety-one").

**Pacing law (unchanged, restated):** 125–145 wpm measured on the final
mix; pace comes from casting, rate, and scripted pauses — **time-stretch
is banned**. Marked pauses count as performance: a first mix that ignores
the marks and lands in-band by reading faster is a fail, not a pass.

---

## 5. The sharpened gate (S2 — rubric + texture checks)

The existing rubric (≥16/20, no zero dimension, scorer ≠ writer —
**now enforced, not aspirational**) stands. Add this measurable panel;
**any single FAIL returns the script**, regardless of rubric total.

| # | Check | Method | Pass |
|---|---|---|---|
| T1 | Hook panel | 5 candidates scored (specificity/address/stakes/curiosity/brevity) | Winner ≥72/100 panel average; no self-resolving winner |
| T2 | Four killers | Audit the winning hook (DELAY/CONFUSION/IRRELEVANCE/DISINTEREST) | 0 flags |
| T3 | Question ladder | Count genuine spoken questions; map question-in/out per scene | ≥1 per scene (Shorts/explainer) or ≥1 per chapter + re-plants (long-form); every scene has named in/out |
| T4 | But/therefore chain | Storyboard connectors written literally | 100% BUT/THEREFORE; 0 "and then" joints |
| T5 | Template repetition | Compare scene shapes/openers | No shape repeats >2 consecutive scenes; no opener pattern repeats in adjacent scenes |
| T6 | Jagged edge | Sentence-length stats from the script text | σ ≥ 4.5 words; no 3 consecutive sentences within ±2 words; ≥2 fragments ≤4 words per scene; median 8–14 |
| T7 | So-what test | One-line stake per scene in the storyboard | Every scene has a stake that names a consequence (breaks/costs/enables) — "interesting" fails |
| T8 | Agency ratio | Count subject action verbs vs copulas per scene | Actions > copulas in every scene |
| T9 | Pivot ration | Count negative pivots; apply earned/hollow test | ≤2/episode, ≤1/scene, all earned (concrete Y, delivered ≤30 s) |
| T10 | Delivery marks | Count `[PAUSE]`/`[ASIDE]`/emphasis marks | ≥1 `[PAUSE]` per scene; asides per character bible cadence; every verdict line carries `[SLOW]` or a lead-in `[PAUSE]` |
| T11 | Slop lint | §6 blacklist scan (script text) | 0 hits (character-bible exceptions noted in the score sheet) |
| T12 | Number audit | Every number has spoken form + `say:` note | 100% |

Enforcement notes: T1–T12 are cheap to check mechanically or by a second
agent; record results alongside the rubric in `03_script_scores.md`.
**Self-scoring a script you wrote caps the recorded total at 15/20** — an
independent scorer is required to certify a pass.

---

## 6. Slop-phrase blacklist (narration text — zero tolerance)

**Meta-narration / YouTuber filler:** "in this video", "today we will /
we'll be looking at", "let's dive in / delve / explore / unpack", "without
further ado", "welcome back", "hey guys", "smash that subscribe", "stay
tuned", "you won't believe", "let that sink in", "read that again",
"this changes everything".

**Throat-clearing openers:** "It is important to note", "Interestingly,",
"It turns out that" as an opener, "In a world where…", "When it comes to…",
"At the end of the day".

**Dead transitions:** "Furthermore", "Additionally", "Moreover",
"With that in mind", "That said" — transitions must do logical work
(but / therefore / so / which means) or be cut.

**Significance inflation (on ordinary facts):** "crucial", "pivotal",
"game-changer", "revolutionary", "remarkable" (unearned), "testament to",
"plays a vital role in", "serves as a reminder". State the fact; let the
viewer weigh it.

**Bloated verbs:** "serves as", "stands as", "boasts", "represents a",
"marks a" → use *is / has / uses / gives / shows / causes*.

**Banned metaphor verbs:** "unpacked", "distilled", "woven", "layered",
"baked in", "bolted on", "crystallised", "sculpted", "anchored" — replace
with literal verbs (cut, added, caused, showed, named, chose).

**Structural slop:** rule-of-three by reflex (if the real count is 2 or 4,
use it), false ranges ("from tiny… to enormous…" with no middle), elegant
variation (renaming the subject every sentence to avoid repetition —
repeat the name), participle fake-depth ("…, highlighting its importance",
"…, paving the way for…").

**Character exceptions (Archivist, rationed, logged in the score sheet):**
the *Filed under: …* sign-off frame; the dry pivot within §2.4's ration;
object-address ("You were sold as 'emerald'…") — each is a fingerprint,
not a habit, and each is counted at the gate.
