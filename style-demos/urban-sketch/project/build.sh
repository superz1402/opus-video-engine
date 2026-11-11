#!/bin/sh
# One-command build for the Urban Sketch 2-min style demo.
# LIB = upstream lemo-opuscar clone. Voice must already exist in voice/actions/
# (GitHub Actions opus-voice run 43001949810; see BUILD-REPORT.md). Rebuild the
# timeline first if voice timings change:  python3 make_timeline.py
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$HOME/workspace/research/nvidia-spy-doc/lemo-opuscar-upstream}
export LIB
: "${PLAYWRIGHT_CHROME:?PLAYWRIGHT_CHROME must point at the Chromium binary}"
export PLAYWRIGHT_CHROME
OUT=$(dirname "$HERE")
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the library folder"; exit 1; }
cd "$LIB"
node core/render/events.mjs "$HERE"
node core/render/video.mjs "$HERE" --fps 24 --workers 3 --out "$HERE/out/video.mp4"
"${PY:-python3}" "$HERE/mix.py"
python3 core/render/srt.py "$HERE/cues.json" "$OUT/demo-2min.srt"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$OUT/demo-2min.mp4" 24 0
echo "DONE: $OUT/demo-2min.mp4"
