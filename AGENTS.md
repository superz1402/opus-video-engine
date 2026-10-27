# AGENTS.md — Opus Video Engine Operating Contract

**You are the operator of this engine. A fresh agent reading only this repo
must be able to run a production end-to-end from this file plus
`engine/ENGINE.md`. The owner (Bilal) does no production work: he approves
finished videos and performs account-holder-only steps. Never ask him for
anything else.**

## What this engine is

A pipeline that turns a topic into a finished narrated explainer video using
the **Opus-5.5 method** (evidence base:
[yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)
— 703 prompts from videos made by asking a coding model to write the
animation as code). The method in one line: **deterministic code animation
(single HTML, pure `seek(t)`) + TTS with word timings + verification loops.**
There is no generative-video model in the loop; do not add one as the
visual spine (one archive entry used it as a garnish layer under JS
animation — the exception, not the method).

Key patterns absorbed from the archive, by creator:

- **@AstroTheWizard (photon-journey explainer):** the full autonomous
  blueprint — script, TTS, captions, per-scene score, ducked mix, streaming
  loudness — and its law: *"Build verification loops: render stills of every
  scene and review them critically… Don't hand me a first draft."* Quality =
  *"code-rendered: crisp, precise, with a coherent design system and one
  strong formal idea per scene."* Also: simulate the real phenomenon, use
  real numbers, state honest uncertainty.
- **@HenrygSing (Kurzgesagt-style explainer):** **STORYBOARD.md first** —
  every scene specified with time, picture, on-screen text, transition —
  approved before scene code; narration via Microsoft (Edge) TTS.
- **@twoclipping (deterministic rendering):** *"Every style is computed
  from time inside seek(t): no CSS transitions, no timers, no state carried
  between frames"*; closed-form springs so motion is a pure function of
  time; render one frame per beat before the full render; written gotchas
  (text blur under camera scale, loop-frame identity, subframe ghosting).
- **@l3d1c (Remotion launch ad):** ~20 stills tiled into **one contact
  sheet** to QA a whole cut at a glance *before* rendering video; every cut
  on a beat grid; one codebase → many cuts/formats.
- **@HenriToivar (HyperFrames explainer):** zero video/image assets,
  code-generated music/SFX, narration + infographics with "consistent
  deterministic output" — proof the no-assets route is a feature, not a
  limitation.

## The workflow (stages — each stage's artifact is a resumable contract)

```
P0 Brief        projects/<slug>/project.json + STORYBOARD.md drafted
P1 Storyboard   STORYBOARD.md locked: per scene — time, picture, on-screen
                text, narration, transition, ONE formal idea, PLUS the
                Script Standard fields: BUT/THEREFORE joint from the
                previous scene, question-in → answer → question-out,
                so-what stake. Facts listed with sources at the foot of
                the storyboard.
P1.5 Script     The narration passes the Script Standard
  gate          (docs/script-standard.md) BEFORE any voice work:
                (a) the retention rubric ≥16/20, no zero dimension, scored
                by an INDEPENDENT scorer — the writer never certifies
                their own script (a self-scored total caps at 15/20);
                (b) the mechanical panel — engine/script_gate.py
                (T3/T5/T6/T9/T10/T11 + hook and pace heuristics), run in
                CI by .github/workflows/script-gate.yml; (c) scorer
                checks T1/T2/T4/T7/T8/T12 recorded in the project's
                score sheet. Any FAIL = rewrite, not produce. The gate
                report is filed in the project (script-gate-report.*).
P2 Voice        voice-input.txt (VOICE:/RATE: directives + narration blocks)
                → engine/voice_tts.py (local clean network or Actions
                voice.yml) → <stem>.audio.wav + .words.json + .timing.json
P3 Animation    index.html — single self-contained file, window.__seek(t)
                (contract in engine/ENGINE.md). Events locked to the P2
                word timings. Design system declared in the storyboard
                (palette/type/accents) and used consistently.
P4 Contact QA   capture stills across every scene → contact sheet →
                INSPECT → written fix list → fix → re-sheet. Minimum one
                full loop, documented in the project's BUILD-REPORT.md.
                No full render before this loop passes.
P5 Render       engine/capture.py (30 fps JPEG frames) → engine/assemble.py
                (frames + narration [+ music] → master CRF 17 + 720p
                review encode), loudnorm −14 LUFS measured two-pass.
P6 Check        ffprobe specs; freezedetect/blackdetect spot checks;
                loudness readback; caption spot-check against words.json;
                claim-vs-facts diff against the storyboard's fact list.
P7 Release      GitHub Release (tag video-<slug>-v<X.Y.Z>) with master +
                review encode attached; run record in runs/. A video is
                not "done" until its Release exists.
```

On GitHub Actions, P1.5's mechanical panel runs as `script-gate.yml`
(on script pushes + dispatch), P2 runs as `voice.yml` and P3–P7 as
`render.yml` (the render job synthesises voice in-job unless given a
prior voice run id). **Actions is the production floor for internet-bound
stages** (Edge TTS needs clean egress); design, storyboarding and gates
are agent work and can happen anywhere.

## Hard rules — breaking any of these is a failed run

1. **Deterministic only.** All animation state derives from `t` inside
   `seek(t)`. No `Date.now()`, no `Math.random()` without a seeded PRNG
   keyed on `t`, no CSS transitions/animations, no timers, no accumulated
   state between frames. A frame rendered twice must be pixel-identical.
2. **Storyboard before code.** No scene is coded before its storyboard row
   exists (time, picture, text, narration, transition, formal idea).
3. **Contact sheet before full render.** P4 is a gate, not a suggestion.
   The fix list and the re-sheet are recorded in BUILD-REPORT.md.
4. **No text-still scenes as hero visuals.** On-screen text supports drawn
   diagrams/animation; a scene whose content is typography alone fails —
   the audience came to *see* the thing. (Kinetic type as a *device*
   inside a drawn scene is fine.)
5. **Facts are sourced.** Every factual claim in narration appears in the
   storyboard's fact list with a source. Species-variable or uncertain
   numbers are hedged in the script itself, never silently sharpened.
6. **Voice is cast, never corrected.** Pace/character come from the
   VOICE:/RATE: directives at synthesis. Time-stretching narration
   (`atempo` etc.) is banned. Word timings come from WordBoundary capture
   (real), or — for a documented local fallback engine — a labelled
   estimate; never present an estimate as measured.
7. **Licences logged.** Any external asset (music, font, image) carries
   name + licence + source in the project's `assets/` notes or storyboard.
   No licence string → the asset does not ship.
8. **Secrets.** Never commit `.env`, tokens, or keys; never paste a
   credential into a file, commit, or chat. CI uses `GITHUB_TOKEN` only.
9. **Honesty of status.** Mark unproven things UNPROVEN. A failed render
   or blocked API is reported with the exact error, in the run record and
   the build report. A placeholder video is never shipped as a run result.
10. **Human-approval gate.** Nothing publishes to any platform before the
    owner approves the exact final file. GitHub Releases in this repo are
    the review shelf (pre-release by default), not public publishing.
11. **Script gate before voice.** No script reaches P2 without a passing
    P1.5 gate on file: the Script Standard (docs/script-standard.md) is
    law, the mechanical panel (engine/script_gate.py) must report no hard
    FAIL, and the rubric must be certified by an independent scorer —
    self-scored totals cap at 15/20 and can never pass a script alone.
    A flat, unmarked, question-free script is a failed script, however
    accurate its facts are.

## Environment notes (proven)

- Local reference VM: Python 3.12 · Node 24 · ffmpeg 8.1 · 2 cores / 7.7 GB
  / no GPU. Playwright Chromium is cached under `~/.cache/ms-playwright`
  (capture.py auto-detects it). Vendor JS/CSS locally in each composition —
  headless Chrome on proxied networks cannot fetch CDNs; on Actions the
  network is clean, but vendoring keeps local == CI.
- Edge TTS on the proxied local VM is **blocked** (WebSocket handshake) —
  that is what Actions `voice.yml` exists for. Local fallback used for the
  first project: Kokoro (Apache-2.0 weights) per-line WAVs + labelled
  proportional timings — a fallback, never the standard.
- Renders are frame-by-frame JPEG screenshots (Playwright) — budget
  ~0.1–0.2 s/frame on 2 cores; a 90 s @ 30 fps video ≈ 2,700 frames.

## Run records (`runs/`)

Every workflow commits `runs/<workflow>/<run-id>/status.json` (+ timings /
probe; render runs also carry one `contact-sheet.jpg` ≤ ~500 KB so an
agent can *see* QA evidence through git). Media rule: full audio lives in
run artifacts, videos live on Releases — never in git. Records are
append-only; read the newest `status.json` for a workflow's last result.
`runs/**` matches no workflow's push paths, so records cannot retrigger.
