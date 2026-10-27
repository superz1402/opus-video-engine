# PROJECT — centipede-vs-human

**"Why a Centipede Body Is Different From Human"** — the Opus Video
Engine's first production, and its proof run: the same project built
twice, once locally (reference build in the originating workspace) and
once end-to-end on GitHub Actions by `render.yml`, so the two masters can
be compared frame-for-frame. Same storyboard, same narration text, same
animation file — the CI build differs only in voice route (production
Edge TTS Sonia vs the local Kokoro fallback) and render machine.

## Artifacts

| Artifact | State |
|---|---|
| `STORYBOARD.md` | ✅ Locked — 8 scenes, ~220 words ≈ 85 s, facts sourced at foot |
| `voice-input.txt` | ✅ Locked — `VOICE: en-GB-SoniaNeural` / `RATE: -3%`, 8 blocks = 8 scenes |
| `index.html` | ⏳ Ingested from the local build when its capture contract is ready (`window.__seek(t)`, 1920×1080 Canvas 2D) |
| `timings.json` | Reference timings from the local fallback synthesis (per-scene starts/durations); CI regenerates its own from the Edge run |
| Actions master | Via `render.yml` → Release `video-centipede-v1.0.0` |

## Scenes (one formal idea each)

1. **Hook** — leg-pair count-up (always odd) vs the human's one pair
2. **Segments** — one module repeated vs a few specialised regions
3. **Weapons** — the fangs are legs (forcipules), drawn morphing leg → claw
4. **Nervous system** — a ganglion chain vs one brain + one cord (X-ray)
5. **Breathing** — spiracles → tracheae → tissue; no lungs, blood carries no O₂
6. **Heart** — a body-length tube pulsing in waves vs one 4-chamber pump
7. **Senses** — near-blind eyespots, antennae first vs eyes first
8. **Close** — two engineering philosophies: repeat the module / centralise & specialise
