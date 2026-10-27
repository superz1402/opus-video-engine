#!/usr/bin/env python3
"""assemble.py — frames + narration → master MP4 (+ 720p review), −14 LUFS.

Two-pass loudnorm on the narration (measure, then apply measured values)
per the opus method's streaming-loudness standard. Optional music bed is
looped/trimmed to picture length and ducked under narration with
sidechaincompress. Video tail: the final frame is held for --tail seconds
of silence so the last word never kisses the cut.

Usage:
  python engine/assemble.py --frames build/frames \
      --audio projects/<slug>/voice-input.audio.wav \
      --out out/<slug>_master.mp4 --review out/<slug>_review_720p.mp4 \
      [--music bed.mp3] [--fps 30] [--tail 1.0]

Requires ffmpeg/ffprobe on PATH.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def probe_duration(path: str) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path])
    return float(r.stdout.strip())


def measure_loudnorm(wav: str) -> dict:
    """First loudnorm pass: returns the measured stats dict."""
    r = subprocess.run(
        ["ffmpeg", "-nostdin", "-i", wav, "-af",
         "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True)
    err = r.stderr
    start = err.rfind("{")
    if start < 0:
        raise RuntimeError("loudnorm measurement produced no JSON")
    return json.loads(err[start:err.rfind("}") + 1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--frames", required=True, help="dir of frame_%05d.jpg")
    ap.add_argument("--audio", required=True, help="narration wav")
    ap.add_argument("--out", required=True)
    ap.add_argument("--review", default="")
    ap.add_argument("--music", default="")
    ap.add_argument("--music-volume", type=float, default=0.16)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--tail", type=float, default=1.0)
    args = ap.parse_args()

    frames = sorted(glob.glob(os.path.join(args.frames, "frame_*.jpg")))
    if not frames:
        print(f"error: no frames in {args.frames}", file=sys.stderr)
        return 2
    if not os.path.isfile(args.audio):
        print(f"error: audio not found: {args.audio}", file=sys.stderr)
        return 2
    n = len(frames)
    pic_dur = n / args.fps
    aud_dur = probe_duration(args.audio)
    total = pic_dur + args.tail
    print(f"assemble: {n} frames = {pic_dur:.2f}s picture, narration "
          f"{aud_dur:.2f}s, total {total:.2f}s (tail {args.tail}s)")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        # 1) silent picture track, final frame held for the tail
        silent = os.path.join(td, "silent.mp4")
        run(["ffmpeg", "-nostdin", "-y", "-framerate", str(args.fps),
             "-i", os.path.join(args.frames, "frame_%05d.jpg"),
             "-vf", f"tpad=stop_mode=clone:stop_duration={args.tail}",
             "-frames:v", str(int(round(total * args.fps))),
             "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
             "-r", str(args.fps), silent])

        # 2) narration → measured loudnorm −14 LUFS
        stats = measure_loudnorm(args.audio)
        ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:"
              f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
              f"measured_LRA={stats['input_lra']}:"
              f"measured_thresh={stats['input_thresh']}:"
              f"offset={stats['target_offset']}:linear=true")
        voice = os.path.join(td, "voice.wav")
        run(["ffmpeg", "-nostdin", "-y", "-i", args.audio, "-af",
             f"apad=whole_dur={total},{ln}", "-ac", "1", "-ar", "48000",
             "-c:a", "pcm_s16le", voice])

        # 3) mux (with optional ducked music bed)
        if args.music and os.path.isfile(args.music):
            bed = os.path.join(td, "bed.wav")
            run(["ffmpeg", "-nostdin", "-y", "-stream_loop", "-1",
                 "-i", args.music, "-t", str(total), "-af",
                 f"volume={args.music_volume},afade=t=in:st=0:d=1.5,"
                 f"afade=t=out:st={max(total - 2, 0)}:d=2",
                 "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", bed])
            run(["ffmpeg", "-nostdin", "-y", "-i", silent, "-i", voice,
                 "-i", bed, "-filter_complex",
                 "[1:a][2:a]sidechaincompress=threshold=0.03:ratio=8:"
                 "attack=40:release=400[ducked];"
                 "[1:a][ducked]amix=inputs=2:duration=first[a]",
                 "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "192k", "-shortest", args.out])
        else:
            run(["ffmpeg", "-nostdin", "-y", "-i", silent, "-i", voice,
                 "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "192k", "-shortest", args.out])
    print(f"master: {args.out} ({os.path.getsize(args.out) / 1e6:.1f} MB)")

    if args.review:
        run(["ffmpeg", "-nostdin", "-y", "-i", args.out, "-vf",
             "scale=1280:720", "-c:v", "libx264", "-crf", "23",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
             args.review])
        print(f"review: {args.review} ({os.path.getsize(args.review) / 1e6:.1f} MB)")
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
