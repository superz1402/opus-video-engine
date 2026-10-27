#!/usr/bin/env python3
"""capture.py — deterministic frame renderer for Opus Video Engine projects.

Loads a project index.html (pure seek(t) contract — see ENGINE.md) in
headless Chromium via Playwright and screenshots every frame as JPEG:
frame = hook(t) exactly, no wall-clock anywhere in the loop.

Usage:
  python engine/capture.py --html projects/<slug>/index.html \
      --out build/frames [--duration 88.4] [--fps 30] \
      [--width 1920] [--height 1080] [--exe /path/to/chrome] [--force]

Duration: --duration wins; else window.__duration is read from the page.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

HOOKS = ["__seek", "seek", "renderFrame"]


def find_chromium() -> str | None:
    pats = [
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
        os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/chrome-linux/headless_shell"),
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/headless_shell"),
    ]
    for p in pats:
        hits = sorted(glob.glob(p))
        if hits:
            return hits[-1]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=float, default=0.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--exe", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.html):
        print(f"error: html not found: {args.html}", file=sys.stderr)
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("error: playwright not installed (pip install playwright)",
              file=sys.stderr)
        return 2

    os.makedirs(args.out, exist_ok=True)
    url = "file://" + os.path.abspath(args.html)
    exe = args.exe or find_chromium()
    launch_kw = {"args": ["--no-sandbox", "--disable-dev-shm-usage",
                          "--force-color-profile=srgb"]}
    if exe:
        launch_kw["executable_path"] = exe

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_kw)
        page = browser.new_page(viewport={"width": args.width,
                                          "height": args.height},
                                device_scale_factor=1)
        page.goto(url)
        hook = page.evaluate(
            """() => { for (const h of %s) if (typeof window[h] === 'function') return h; return null; }"""
            % HOOKS)
        if not hook:
            # give async compositions a moment to install the hook
            for _ in range(50):
                page.wait_for_timeout(200)
                hook = page.evaluate(
                    """() => { for (const h of %s) if (typeof window[h] === 'function') return h; return null; }"""
                    % HOOKS)
                if hook:
                    break
        if not hook:
            print("error: no seek hook (__seek/seek/renderFrame) on page",
                  file=sys.stderr)
            browser.close()
            return 1
        duration = args.duration or page.evaluate(
            "() => (typeof window.__duration === 'number' ? window.__duration : 0)")
        if not duration:
            print("error: no duration — pass --duration or set window.__duration",
                  file=sys.stderr)
            browser.close()
            return 1
        total = int(round(duration * args.fps))
        print(f"capture: hook={hook} duration={duration:.2f}s fps={args.fps} "
              f"frames={total} -> {args.out}", flush=True)

        seek_js = """async (t) => {
            window['%s'](t);
            await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
        }""" % hook
        done = 0
        for i in range(total):
            path = os.path.join(args.out, f"frame_{i:05d}.jpg")
            if os.path.exists(path) and not args.force:
                done += 1
                continue
            page.evaluate(seek_js, i / args.fps)
            page.screenshot(path=path, type="jpeg", quality=90)
            done += 1
            if done % 60 == 0:
                print(f"  {done}/{total}", flush=True)
        browser.close()
    print(f"DONE: {done} frames in {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
