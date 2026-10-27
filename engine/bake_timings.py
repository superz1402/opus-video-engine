#!/usr/bin/env python3
"""bake_timings.py — inject measured voice timings into a project template.

Projects whose animation events are keyed to word timings ship
`index.template.html` with two placeholders:

  const TIMINGS   = /*__TIMINGS__*/;
  const SENTENCES = /*__SENTENCES__*/;

This tool replaces them with a timings object built from a REAL synthesis
run — engine/voice_tts.py outputs (<stem>.words.json + <stem>.timing.json)
— so the baked animation is locked to the voice that will actually be
mixed in, on any machine. (The originating pattern is the centipede
project's build_html.py; this is its generalised engine form.)

Block i of the timing file == scene i (voice-input blocks are written
one-per-scene — see templates). Sentence spans are derived from the word
timings by terminal punctuation, exactly like the original builder.

Usage:
  python engine/bake_timings.py \
      --template projects/<slug>/index.template.html \
      --words    projects/<slug>/voice-input.words.json \
      --timing   projects/<slug>/voice-input.timing.json \
      --out      build/<slug>/index.html
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys


def build_timings(words: list[dict], timing: dict) -> dict:
    blocks = sorted(timing.items(), key=lambda kv: kv[1]["start"])
    scenes = []
    for i, (bid, b) in enumerate(blocks, 1):
        start, dur = b["start"], b["dur"]
        scene_words = [
            {"w": w["w"], "start": round(w["t"], 3),
             "end": round(w["t"] + w["d"], 3)}
            for w in words if start - 0.01 <= w["t"] < start + dur + 0.01
        ]
        scenes.append({"scene": i, "file": "", "text": b["text"],
                       "start": round(start, 3), "dur": round(dur, 3),
                       "end": round(start + dur, 3), "words": scene_words})
    total = scenes[-1]["end"] if scenes else 0.0
    return {"voice": "engine/voice_tts.py (Edge TTS, measured WordBoundary)",
            "total_s": round(total, 3), "scenes": scenes}


def build_sentences(timings: dict) -> list[dict]:
    sentences = []
    for sc in timings["scenes"]:
        cur: list[dict] = []
        for w in sc["words"]:
            cur.append(w)
            if re.search(r"[.!?]$", w["w"]):
                sentences.append({"text": " ".join(x["w"] for x in cur),
                                    "start": cur[0]["start"],
                                    "end": cur[-1]["end"]})
                cur = []
        if cur:
            sentences.append({"text": " ".join(x["w"] for x in cur),
                              "start": cur[0]["start"],
                              "end": cur[-1]["end"]})
    return sentences


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--template", required=True)
    ap.add_argument("--words", required=True)
    ap.add_argument("--timing", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    for p in (args.template, args.words, args.timing):
        if not os.path.isfile(p):
            print(f"error: not found: {p}", file=sys.stderr)
            return 2
    words = json.load(open(args.words, encoding="utf-8"))
    timing = json.load(open(args.timing, encoding="utf-8"))
    timings = build_timings(words, timing)
    sentences = build_sentences(timings)

    tpl = open(args.template, encoding="utf-8").read()
    if "/*__TIMINGS__*/" not in tpl or "/*__SENTENCES__*/" not in tpl:
        print("error: template is missing /*__TIMINGS__*/ or "
              "/*__SENTENCES__*/ placeholders", file=sys.stderr)
        return 1
    html = tpl.replace("/*__TIMINGS__*/", json.dumps(timings))
    html = html.replace("/*__SENTENCES__*/", json.dumps(sentences))
    assert "/*__" not in html, "unreplaced placeholder remains"
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    open(args.out, "w", encoding="utf-8").write(html)
    print(f"baked {args.out} ({len(html)} bytes): {len(timings['scenes'])} "
          f"scenes, {len(sentences)} caption sentences, "
          f"total_s={timings['total_s']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
