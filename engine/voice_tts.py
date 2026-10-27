#!/usr/bin/env python3
"""voice_tts.py — Opus Video Engine narration (Edge TTS, Actions-first).

This is the PRODUCTION voice path for the Opus Video Engine. It is designed
to run on a GitHub Actions runner, where egress is unrestricted, so it needs
NO proxy hacks, NO combined CA bundles, and NO monkeypatching: on a clean
network plain edge-tts just works. (On a proxied local VM, Edge synthesis is
blocked at the WebSocket handshake — run voice on Actions, or use a local
fallback engine and import the WAVs; see AGENTS.md.)

Pattern adapted from Bilal's own opuscar-studio
``work/video-004-dyatlov-pass/src/gen_tts_andrew.py`` (house voice contract):
per-block synthesis, WordBoundary capture for caption timing, trailing-silence
trim to a fixed pad, resumable per-block outputs, retries with backoff, and a
timing ledger. Differences from the opuscar original, by design:

* Input is a plain-text / simple-markdown script file, not a narration.json.
  Blocks are paragraphs (blank-line separated); a block longer than
  ``--max-chars`` is split at sentence boundaries so no single synthesis call
  carries a whole scene.
* Markdown dressing (``#`` headings, ``**bold**``, ``[STAGE DIRECTIONS]`` and
  ``<!-- comments -->``) is stripped before synthesis — stage directions are
  for humans and the editor, never for the voice.
* Optional DIRECTIVE lines at the very top of the input file (casting /
  audition support) are read as operator instructions and never spoken:
  ``VOICE: <edge-voice>`` and ``RATE: <-3%>`` override the CLI/workflow
  values — push-triggered runs always carry the workflow's default voice
  flag, so a per-file casting (e.g. a voice audition committed to
  ``.github/smoke/tts.txt``) needs this route. ``AUDIO-TO-RUNS: yes``
  additionally writes ``runs/voice-tts/<GITHUB_RUN_ID>/audio-<voice>.json``
  (voice, rate, base64 of a 64 kbps MP3 of the finished narration) so the
  workflow's run-record commit carries listenable audition audio back —
  the connector cannot download Actions artifacts, and ``*.mp3``/``*.wav``
  are gitignored by design; production episode runs never set it, so
  episode audio still lives only in run artifacts / Releases.
* Outputs land NEXT TO the input file (``<stem>.audio.wav``,
  ``<stem>.words.json``, ``<stem>.timing.json``, plus a ``<stem>.blocks/``
  directory of per-block wavs/word files) instead of a fixed ``audio/`` tree,
  so one workflow run can voice any episode's script in place.
* ``words.json`` is the merged, episode-level word-timing file: absolute
  offsets (seconds) across the concatenated narration, in playback order —
  the exact contract S6 caption generation consumes.

Output formats (all next to the input script):
  <stem>.audio.wav     pcm_s16le, 24 kHz, mono — full narration, blocks
                       joined with ``--gap`` seconds of silence (default 0.35)
  <stem>.words.json    [{"t": start_s, "d": dur_s, "w": "word"}, ...]
  <stem>.timing.json   {block_id: {"dur": s, "start": s, "text": ...}}
  <stem>.blocks/       per-block <id>.wav + <id>.words.json (resumability)

Usage (Actions and anywhere with clean egress):
  python engine/voice_tts.py projects/centipede-vs-human/voice-input.txt
  python engine/voice_tts.py script.md --voice en-US-AndrewMultilingualNeural --rate -3%
  python engine/voice_tts.py script.txt --force        # redo every block
  python engine/voice_tts.py script.txt --only b003,b007

House voice (docs/channel-bible.md §Voice): en-US-AndrewMultilingualNeural
at -3% (-4% long-form). PACING LAW: the rate is a casting choice made here —
never "fix" pace later with atempo/time-stretch (AGENTS.md rule 16).

Requires: edge-tts (pip), ffmpeg + ffprobe on PATH.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time

DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"
DEFAULT_RATE = "-3%"
SYNTH_TIMEOUT = 90          # seconds per attempt — edge-tts can hang mid-stream
MAX_ATTEMPTS = 4
BLOCK_GAP_S = 0.35          # silence between blocks in the joined narration
TAIL_PAD_S = 0.25           # kept tail after trailing-silence trim (opuscar)
MAX_BLOCK_CHARS = 600       # split longer paragraphs at sentence boundaries


# --------------------------------------------------------------------------
# Script parsing
# --------------------------------------------------------------------------

def clean_block(text: str) -> str:
    """Strip markdown/stage dressing so only spoken words reach the voice."""
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)          # comments
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)    # headings
    text = re.sub(r"\[[^\]]*\]", " ", text)                      # [ASIDE] etc.
    text = re.sub(r"(\*\*|__|\*|_|`)", "", text)                 # emphasis/code
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)         # list bullets
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str, max_chars: int) -> list[str]:
    """Greedy sentence packing: no chunk longer than max_chars (hard-split if
    a single sentence exceeds it — better an ugly split than a failed call)."""
    sentences = re.split(r"(?<=[.!?…])\s+", text)
    chunks: list[str] = []
    cur = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        while len(s) > max_chars:                       # pathological sentence
            cut = s.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            chunks.append(s[:cut].strip())
            s = s[cut:].strip()
        if cur and len(cur) + 1 + len(s) > max_chars:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    return chunks


DIRECTIVE_RE = re.compile(r"^\s*(VOICE|RATE|AUDIO-TO-RUNS)\s*:\s*(\S.*?)\s*$",
                          re.IGNORECASE)


def parse_directives(raw: str) -> tuple[dict, str]:
    """Split leading DIRECTIVE lines off the raw script text.

    Directives are operator instructions (casting / audition), never
    narration: only a run of matching lines at the very top of the file is
    recognized, and those lines are removed before block parsing.
    """
    directives: dict = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        m = DIRECTIVE_RE.match(lines[i])
        if not m:
            break
        directives[m.group(1).upper()] = m.group(2)
        i += 1
    return directives, "\n".join(lines[i:])


def load_blocks(path: str, max_chars: int) -> tuple[list[dict], dict]:
    raw = open(path, encoding="utf-8").read()
    directives, raw = parse_directives(raw)
    blocks: list[dict] = []
    for para in re.split(r"\n\s*\n", raw):
        cleaned = clean_block(para)
        if not cleaned:
            continue
        for chunk in split_sentences(cleaned, max_chars):
            blocks.append({"id": f"b{len(blocks) + 1:03d}", "text": chunk})
    return blocks, directives


# --------------------------------------------------------------------------
# Audio helpers (ffmpeg/ffprobe — same approach as the opuscar original)
# --------------------------------------------------------------------------

def probe_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def mp3_to_block_wav(mp3: str, wav: str) -> None:
    """MP3 -> 24 kHz mono WAV, trailing silence trimmed to TAIL_PAD_S."""
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-i", mp3, "-af",
         "silenceremove=start_periods=1:start_threshold=-45dB,"
         "areverse,"
         "silenceremove=start_periods=1:start_threshold=-45dB,"
         f"areverse,apad=pad_dur={TAIL_PAD_S}",
         "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", wav],
        capture_output=True, check=True)


def join_blocks(wavs: list[str], gap_s: float, out: str) -> None:
    """Concatenate block WAVs with fixed silence gaps (concat demuxer).

    All inputs share codec params (pcm_s16le / 24 kHz / mono) by construction,
    so a generated silence file of the same shape slots between them cleanly.
    """
    if len(wavs) == 1 or gap_s <= 0:
        listfile = out + ".concat.txt"
        with open(listfile, "w", encoding="utf-8") as f:
            for w in wavs:
                f.write(f"file '{os.path.abspath(w)}'\n")
        try:
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-f", "concat", "-safe", "0",
                            "-i", listfile, "-c:a", "pcm_s16le", out],
                           capture_output=True, check=True)
        finally:
            os.remove(listfile)
        return
    gap_wav = out + ".gap.wav"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-f", "lavfi",
                    "-i", "anullsrc=r=24000:cl=mono", "-t", str(gap_s),
                    "-c:a", "pcm_s16le", gap_wav],
                   capture_output=True, check=True)
    listfile = out + ".concat.txt"
    try:
        with open(listfile, "w", encoding="utf-8") as f:
            for i, w in enumerate(wavs):
                f.write(f"file '{os.path.abspath(w)}'\n")
                if i < len(wavs) - 1:
                    f.write(f"file '{os.path.abspath(gap_wav)}'\n")
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-f", "concat", "-safe", "0",
                        "-i", listfile, "-c:a", "pcm_s16le", out],
                       capture_output=True, check=True)
    finally:
        for p in (listfile, gap_wav):
            if os.path.exists(p):
                os.remove(p)


# --------------------------------------------------------------------------
# Synthesis (edge-tts, WordBoundary capture — opuscar contract)
# --------------------------------------------------------------------------

async def synth_block(text: str, voice: str, rate: str, mp3_path: str) -> list[dict]:
    import edge_tts  # imported here so --help works without the dependency

    words: list[dict] = []
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    with open(mp3_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({"t": chunk["offset"] / 1e7,
                              "d": chunk["duration"] / 1e7,
                              "w": chunk["text"]})
    return words


def synth_with_retries(text: str, voice: str, rate: str, mp3_path: str) -> list[dict]:
    last_err: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            words = asyncio.run(asyncio.wait_for(
                synth_block(text, voice, rate, mp3_path), timeout=SYNTH_TIMEOUT))
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1000:
                return words
            raise RuntimeError("synthesis produced no usable audio")
        except Exception as e:  # noqa: BLE001 — retry any transport/TTS failure
            last_err = e
            print(f"    attempt {attempt + 1}/{MAX_ATTEMPTS} failed: {e}", flush=True)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"all {MAX_ATTEMPTS} attempts failed: {last_err}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("script", help="plain-text or simple-markdown script file")
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help=f"Edge TTS voice (default: {DEFAULT_VOICE})")
    ap.add_argument("--rate", default=DEFAULT_RATE,
                    help="prosody rate such as -3 percent (house default: minus 3)")
    ap.add_argument("--gap", type=float, default=BLOCK_GAP_S,
                    help=f"silence between blocks, seconds (default: {BLOCK_GAP_S})")
    ap.add_argument("--max-chars", type=int, default=MAX_BLOCK_CHARS,
                    help=f"max characters per synthesis block (default: {MAX_BLOCK_CHARS})")
    ap.add_argument("--force", action="store_true",
                    help="re-synthesize blocks even if outputs already exist")
    ap.add_argument("--only", default="",
                    help="comma-separated block ids to synthesize (e.g. b003,b007)")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.script):
        print(f"error: script not found: {args.script}", file=sys.stderr)
        return 2
    for tool in ("ffmpeg", "ffprobe"):
        if subprocess.run(["which", tool], capture_output=True).returncode != 0:
            print(f"error: {tool} not on PATH", file=sys.stderr)
            return 2

    script_dir = os.path.dirname(os.path.abspath(args.script))
    stem = os.path.splitext(os.path.basename(args.script))[0]
    blocks_dir = os.path.join(script_dir, f"{stem}.blocks")
    os.makedirs(blocks_dir, exist_ok=True)
    tmp_mp3 = os.path.join(blocks_dir, "_tmp.mp3")

    blocks, directives = load_blocks(args.script, args.max_chars)
    if not blocks:
        print("error: no speakable text found in script", file=sys.stderr)
        return 2
    if directives.get("VOICE"):
        print(f"directive override: voice {args.voice} -> {directives['VOICE']}",
              flush=True)
        args.voice = directives["VOICE"]
    if directives.get("RATE"):
        print(f"directive override: rate {args.rate} -> {directives['RATE']}",
              flush=True)
        args.rate = directives["RATE"]
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    print(f"{args.script}: {len(blocks)} block(s), voice={args.voice} rate={args.rate}",
          flush=True)

    timing_path = os.path.join(script_dir, f"{stem}.timing.json")
    timing: dict = {}
    if os.path.exists(timing_path) and not args.force:
        try:
            timing = json.load(open(timing_path, encoding="utf-8"))
        except json.JSONDecodeError:
            timing = {}

    fails: list[str] = []
    for i, block in enumerate(blocks):
        bid, text = block["id"], block["text"]
        wav = os.path.join(blocks_dir, f"{bid}.wav")
        wj = os.path.join(blocks_dir, f"{bid}.words.json")
        done = (os.path.exists(wav) and os.path.exists(wj) and bid in timing)
        if done and not args.force and bid not in only:
            print(f"[{i + 1}/{len(blocks)}] {bid} cached — skip", flush=True)
            continue
        if only and bid not in only and done:
            continue
        try:
            words = synth_with_retries(text, args.voice, args.rate, tmp_mp3)
            mp3_to_block_wav(tmp_mp3, wav)
            dur = probe_duration(wav)
            json.dump(words, open(wj, "w", encoding="utf-8"))
            timing[bid] = {"dur": round(dur, 3), "text": text}
            json.dump(timing, open(timing_path, "w", encoding="utf-8"), indent=1)
            print(f"[{i + 1}/{len(blocks)}] {bid} {dur:.1f}s {len(words)} words",
                  flush=True)
        except Exception as e:  # noqa: BLE001 — record and continue other blocks
            print(f"[{i + 1}/{len(blocks)}] {bid} FAILED: {e}", flush=True)
            fails.append(bid)
        finally:
            if os.path.exists(tmp_mp3):
                os.remove(tmp_mp3)
        time.sleep(0.35)

    missing = [b["id"] for b in blocks if b["id"] not in timing]
    if missing or fails:
        print(f"INCOMPLETE: missing/failed blocks: {sorted(set(missing + fails))}",
              file=sys.stderr)
        return 1

    # Join in script order; build absolute-offset timing + merged word timings.
    ordered = [b for b in blocks]
    start = 0.0
    merged_words: list[dict] = []
    for idx, block in enumerate(ordered):
        bid = block["id"]
        dur = timing[bid]["dur"]
        timing[bid]["start"] = round(start, 3)
        words = json.load(open(os.path.join(blocks_dir, f"{bid}.words.json"),
                               encoding="utf-8"))
        for w in words:
            merged_words.append({"t": round(start + w["t"], 3),
                                 "d": w["d"], "w": w["w"]})
        start += dur + (args.gap if idx < len(ordered) - 1 else 0.0)

    out_wav = os.path.join(script_dir, f"{stem}.audio.wav")
    join_blocks([os.path.join(blocks_dir, f"{b['id']}.wav") for b in ordered],
                args.gap, out_wav)
    json.dump(timing, open(timing_path, "w", encoding="utf-8"), indent=1)
    words_path = os.path.join(script_dir, f"{stem}.words.json")
    json.dump(merged_words, open(words_path, "w", encoding="utf-8"))

    total = probe_duration(out_wav)
    print(f"DONE: {len(ordered)} blocks, narration {total:.1f}s, "
          f"{len(merged_words)} timed words")
    print(f"  audio : {out_wav}")
    print(f"  words : {words_path}")
    print(f"  timing: {timing_path}")

    # Audition-only export (directive-gated, see module docstring): carry a
    # listenable MP3 back inside the run record as base64 JSON. Best-effort —
    # an export failure must never fail an otherwise good take.
    if directives.get("AUDIO-TO-RUNS", "").lower() in ("yes", "1", "true"):
        run_id = os.environ.get("GITHUB_RUN_ID")
        if not run_id:
            print("  runs-export skipped: GITHUB_RUN_ID not set (not on Actions)")
        else:
            try:
                import base64
                import tempfile
                repo_root = os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__)))
                rec_dir = os.path.join(repo_root, "runs", "voice", run_id)
                os.makedirs(rec_dir, exist_ok=True)
                slug = re.sub(r"[^a-z0-9]+", "-", args.voice.lower()).strip("-")
                with tempfile.TemporaryDirectory() as td:
                    tmp_mp3 = os.path.join(td, "audition.mp3")
                    subprocess.run(
                        ["ffmpeg", "-nostdin", "-y", "-i", out_wav,
                         "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame",
                         "-b:a", "64k", tmp_mp3],
                        capture_output=True, check=True)
                    payload = base64.b64encode(open(tmp_mp3, "rb").read())
                export = {"voice": args.voice, "rate": args.rate,
                          "source_wav_seconds": round(total, 2),
                          "mp3_64kbps_base64": payload.decode("ascii")}
                out_json = os.path.join(rec_dir, f"audio-{slug}.json")
                json.dump(export, open(out_json, "w", encoding="utf-8"))
                print(f"  runs-export: {out_json}")
            except Exception as e:  # noqa: BLE001 — never fail a take over it
                print(f"  runs-export FAILED (non-fatal): {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
