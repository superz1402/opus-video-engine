#!/usr/bin/env python3
"""contact_sheet.py — tile N evenly spaced frames of a video into one JPEG.

The P4 QA evidence (opus method: judge the whole cut from one sheet before
committing to a full render). Requires ffmpeg/ffprobe on PATH.

Usage: python engine/contact_sheet.py master.mp4 --out sheet.jpg
       [--count 12] [--cols 4] [--width 480]
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def probe_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--count", type=int, default=12)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--width", type=int, default=480)
    args = ap.parse_args()

    dur = probe_duration(args.video)
    if dur <= 0:
        print("error: could not probe duration", file=sys.stderr)
        return 1
    rows = (args.count + args.cols - 1) // args.cols
    # fps filter picks ~count frames across the duration; tile lays them out.
    vf = (f"fps=1/{dur / args.count:.4f},scale={args.width}:-1,"
          f"tile={args.cols}x{rows}:padding=4:margin=4")
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-i", args.video, "-vf", vf,
                    "-frames:v", "1", args.out],
                   capture_output=True, check=True)
    print(f"DONE: {args.out} ({args.count} frames over {dur:.1f}s, "
          f"{args.cols}x{rows})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
