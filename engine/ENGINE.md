# ENGINE.md — machinery reference + the project-HTML contract

## The project-HTML contract (read this before writing any `index.html`)

A project animation is **one self-contained HTML file** (all JS/CSS/assets
inline or vendored beside it in the project folder — no CDN dependencies)
that renders any moment of the video as a pure function of time:

```js
window.__seek = function (tSeconds) { /* draw the frame for time t */ };
// optional but recommended:
window.__duration = 88.4;            // total seconds
```

Capture (`engine/capture.py`) drives it like this:

1. Load the file in headless Chromium at the project's resolution
   (default 1920×1080, deviceScaleFactor 1).
2. Wait until one of the seek hooks exists (checked in order):
   `window.__seek`, `window.seek`, `window.renderFrame`.
3. For each frame `i` at `t = i / fps`: call the hook with `t`, wait two
   `requestAnimationFrame` ticks so the canvas has painted, screenshot.

**Rules for the HTML author** (from AGENTS.md hard rule 1):

- Everything on screen must be computed from `t` inside the seek call:
  no CSS transitions/animations, no `setInterval`/`setTimeout` visuals,
  no state accumulated between calls. Calling `__seek(12.0)` twice must
  produce the identical frame.
- Randomness only via a seeded PRNG re-seeded from `t` (or precomputed
  tables), never `Math.random()` live.
- Size the stage in CSS pixels at the project resolution; capture uses a
  viewport of exactly that size.
- Word-timed events: read the project's `timings.json` (words with
  absolute start/end) at build time and bake the event times into the
  HTML as constants — the page itself must not fetch at render time.
- Keep a `window.__READY = true` assignment after first paint if the
  composition builds assets asynchronously; capture waits for any hook,
  and the double-rAF settle covers the rest.

## CLI reference

### `engine/voice_tts.py <script.txt> [--voice V] [--rate -3%] [--gap 0.35]`

Edge TTS narration (opuscar pattern). Input directives at the top of the
script file override CLI values and are never spoken:

```
VOICE: en-GB-SoniaNeural
RATE: -3%
```

Outputs next to the input: `<stem>.audio.wav` (24 kHz mono PCM),
`<stem>.words.json` (`[{t, d, w}]` absolute word timings),
`<stem>.timing.json` (per-block durations/starts), `<stem>.blocks/`
(per-block WAVs — synthesis is resumable; rerunning skips finished blocks
unless `--force`). Needs clean egress (run on Actions or an open network).

### `engine/capture.py --html index.html --out frames/ [--duration S] [--fps 30] [--width 1920] [--height 1080]`

Playwright frame renderer. Duration resolution order: `--duration` →
`window.__duration` → error. Writes `frame_%05d.jpg` (JPEG q90) into
`--out`. Auto-detects a Chromium executable from `~/.cache/ms-playwright`
or the Playwright-managed install; `--exe` overrides. Prints progress
every 60 frames; safe to rerun (existing frames are skipped unless
`--force`).

### `engine/assemble.py --frames frames/ --audio narration.wav --out master.mp4 [--review review.mp4] [--music bed.mp3] [--music-volume 0.16] [--fps 30] [--tail 1.0]`

Assembles the master: image sequence → H.264 (CRF 17, yuv420p); narration
loudnorm-measured then applied to **−14 LUFS / TP −1.5** (two-pass
`loudnorm`); optional music bed looped/trimmed to length, ducked under
the narration with `sidechaincompress`. `--review` also writes a 720p
encode (CRF 23). The video is padded with `--tail` seconds of held final
frame audio silence so the last word never kisses the cut.

### `engine/contact_sheet.py <video.mp4> --out sheet.jpg [--count 12] [--cols 4]`

Tiles `--count` evenly spaced frames of the video into one JPEG sheet —
the P4 QA evidence. Works on the master (post-render check) or, pointed
at a short preview encode, before committing to full quality settings.

### `engine/new_project.py <slug> [--title "..."] [--format 1920x1080]`

Copies `templates/project/` into `projects/<slug>/`, fills `project.json`
and the storyboard header. Refuses to overwrite an existing project.
