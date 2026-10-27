# CI run — centipede-vs-human (GitHub Actions, 2026-10-27)

The parallel Actions build of this project, run end-to-end by the engine's
workflows on `superz1402/opus-video-engine`.

## Result

- **Release (pre-release):**
  https://github.com/superz1402/opus-video-engine/releases/tag/video-centipede-v1.0.0
  — `centipede-vs-human_master.mp4` (19,098,950 B) +
  `centipede-vs-human_review_720p.mp4` (5,234,879 B).
- **Master specs (ffprobe, verified after download):** H.264 1920×1080
  @ 30 fps, AAC, **98.27 s**, loudness readback **−14.09 LUFS / TP −1.49**.
  Release asset is byte-identical (md5) to the workflow artifact.
- **Voice:** en-GB-SoniaNeural @ −3% (opus-voice run 40474900725),
  8 blocks = 8 scenes, 229 WordBoundary-timed words, 93.6 s of speech;
  scene starts 0 / 15.38 / 28.11 / 38.20 / 51.36 / 64.06 / 72.16 / 83.55 s.
- **Run records:** `runs/voice/40474900725/`, `runs/render/40475114411/`
  (status.json + probe.json + contact sheet) committed by the workflows.

## Run history (all on 2026-10-27)

| Run | Workflow | Outcome |
|---|---|---|
| 40474293829 | opus-voice #1 | success — but only **3 blocks**: the source voice-input separated scenes with single newlines, so sentence-packing merged them |
| 40474496286 | opus-render #1 | cancelled by the operator — the local build landed QA fixes to the HTML mid-flight; re-ingested before re-dispatch |
| 40474622612 | opus-render #2 | failure at the duration step — a human log line was printed into the `$GITHUB_OUTPUT` channel (fixed: logs go to stderr); the step log also exposed the 3-block bake |
| 40474900725 | opus-voice #2 | success — **8 blocks** after the voice-input was rewritten with blank-line-separated scene paragraphs |
| 40475114411 | opus-render #3 | **success** — bake guard (baked scenes == `project.json` scenes) passed, 2,948 frames captured, release published |

Fixes landed from these runs: stderr logging in the duration step, the
bake scene-count guard, the block convention documented in
`engine/ENGINE.md`, `"scenes"` in `project.json`.

## Known differences vs the local reference build

- **Voice:** CI uses the production Edge/Sonia path with *measured*
  WordBoundary timings baked per scene; the local build used the Kokoro
  af_heart offline fallback with proportional-estimate word timings
  (its Edge route is blocked by the local egress proxy). Sonia reads the
  script ~10 s slower: CI total 98.27 s vs local picture ≈ 88.2 s.
- **Mix:** CI is narration-only (no music asset exists in this project);
  the local build composed a music + SFX bed. `engine/assemble.py`
  supports `assets/music.*` ducking when a project ships one.
- **Frames:** same deterministic HTML (incl. the local build's QA fixes);
  CI renders in the runner's Chromium — caption/type rendering matched
  the local contact sheet.
