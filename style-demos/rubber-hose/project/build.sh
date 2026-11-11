#!/bin/sh
# One-command rebuild of the 2-minute rubber-hose style demo.
# Voice must already exist in voice/actions/ (GitHub Actions opus-voice run,
# superz1402/opus-video-engine, run 43001880339 — Swara @ +12%).
# If voice timings change, re-run: python3 make_timeline.py
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$HOME/workspace/research/nvidia-spy-doc/lemo-opuscar-upstream}
export LIB
: "${PLAYWRIGHT_CHROME:?PLAYWRIGHT_CHROME must point at the Chromium binary}"
export PLAYWRIGHT_CHROME
PY=${PY:-$HOME/workspace/research/nvidia-spy-doc/proof/project/.venv/bin/python}
DEMO=$(dirname "$HERE")
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the library folder"; exit 1; }
cd "$LIB"
node core/render/events.mjs "$HERE"
"$PY" "$HERE/music.py"
"$PY" "$HERE/mix.py"
node core/render/video.mjs "$HERE" --fps 24 --workers 3 --out "$HERE/out/video.mp4"
python3 core/render/srt.py "$HERE/cues.json" "$DEMO/demo-2min.srt"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$DEMO/demo-2min.mp4" 24 3
echo "DONE: $DEMO/demo-2min.mp4"
