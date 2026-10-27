# Opus Video Engine

A reusable engine for producing narrated explainer videos **the Opus-5.5 way**:
a strong coding agent writes the whole animation as **deterministic code** —
one self-contained HTML file whose every frame is a pure function of time,
`frame = seek(t)` — and the engine renders it frame-by-frame, synthesises the
narration with word-level timings, mixes to streaming loudness, and QA's the
result with contact sheets before anything is called finished.

There is no video-generation model in this pipeline. The quality comes from
the method (documented in `AGENTS.md`):

1. **Storyboard before code** — every scene specified (time, picture,
   on-screen text, narration, transition) before a line of animation exists.
2. **Deterministic seek(t)** — no CSS transitions, no timers, no state
   carried between frames. Same `t` → same frame, always, so scenes can be
   iterated precisely and rendered identically locally and on CI.
3. **Voice timings drive events** — narration is synthesised per block with
   WordBoundary capture; animation events and captions lock to the measured
   word timings, never to guesses.
4. **Contact-sheet QA loops** — render stills across every scene, inspect,
   fix what's flat/dead/wrong, re-render. *Then* the full render.
5. **Beat-locked cuts, −14 LUFS mix** — cuts land on scene/timing boundaries;
   the final mix is loudnorm-measured to streaming loudness.

Method sources: the prompt archive at
[yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos)
(703 production prompts — see the key patterns cited in `AGENTS.md`), plus
the Actions/Release/run-record conventions proven on
[superz1402/Orb-theory-system](https://github.com/superz1402/Orb-theory-system).

## Layout

```
AGENTS.md                  the operating contract — READ THIS FIRST
engine/
  voice_tts.py             Edge TTS narration (VOICE:/RATE: directives, WordBoundary timings)
  bake_timings.py          bake a measured run's timings into a project's index.template.html
  capture.py               Playwright frame renderer for a project HTML (seek(t) → JPEG frames)
  assemble.py              frames + narration (+ optional music) → master + 720p review, −14 LUFS
  contact_sheet.py         contact sheet from a rendered video (QA evidence)
  new_project.py           scaffold a new project from templates/
  ENGINE.md                the project-HTML contract + CLI reference
projects/<slug>/           one folder per video (storyboard, HTML, voice-input, project.json)
templates/                 storyboard template + project skeleton
runs/<workflow>/<run-id>/  structured run records committed by the workflows
.github/workflows/
  voice.yml                stage: narration on Actions → artifact + run record
  render.yml               stage: full video run on Actions → artifact + GitHub Release + run record
```

## Quickstart

```bash
# 1. Scaffold a project
python engine/new_project.py my-topic --title "Why X Is Not Y"

# 2. Write projects/my-topic/STORYBOARD.md (template provided), then the
#    narration in projects/my-topic/voice-input.txt with directives:
#      VOICE: en-GB-SoniaNeural
#      RATE: -3%

# 3. Build projects/my-topic/index.html — one self-contained HTML file
#    exposing window.__seek(tSeconds) (contract: engine/ENGINE.md).

# 4a. Run it on GitHub Actions (the production floor):
#     Actions → opus-render → Run workflow → project=my-topic
#     → master + review encode land on a GitHub Release + run artifact.
# 4b. Or run it locally (needs a Playwright Chromium + ffmpeg):
python engine/voice_tts.py projects/my-topic/voice-input.txt
python engine/capture.py --html projects/my-topic/index.html --duration 88 --out build/frames
python engine/assemble.py --frames build/frames --audio projects/my-topic/voice-input.audio.wav \
    --out out/my-topic_master.mp4 --review out/my-topic_review_720p.mp4
python engine/contact_sheet.py out/my-topic_master.mp4 --out out/contact-sheet.jpg
```

## Projects

| Project | Topic | Status |
|---|---|---|
| `centipede-vs-human` | Why a centipede body is different from human | First engine production — storyboard locked, Actions run is the parallel CI build of the local reference build |

## Watching runs

- **Actions tab** — every stage, live.
- **Releases tab** — finished videos (master MP4 + 720p review encode).
- **`runs/` in this repo** — structured record of every workflow run
  (`status.json`, timings, probe, contact sheet) — how an agent reads
  results back without the Actions UI.
