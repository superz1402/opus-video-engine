#!/usr/bin/env python3
"""new_project.py — scaffold a project from templates/project/.

Usage: python engine/new_project.py <slug> [--title "Title"] [--format 1920x1080]
Refuses to overwrite an existing project.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("slug")
    ap.add_argument("--title", default="")
    ap.add_argument("--format", default="1920x1080")
    args = ap.parse_args()

    src = os.path.join(ROOT, "templates", "project")
    dst = os.path.join(ROOT, "projects", args.slug)
    if os.path.exists(dst):
        print(f"error: project exists: {dst}", file=sys.stderr)
        return 1
    shutil.copytree(src, dst)

    pj_path = os.path.join(dst, "project.json")
    pj = json.load(open(pj_path, encoding="utf-8"))
    w, h = (int(x) for x in args.format.lower().split("x"))
    pj.update({"slug": args.slug, "title": args.title or args.slug,
               "width": w, "height": h})
    json.dump(pj, open(pj_path, "w", encoding="utf-8"), indent=1)

    sb = os.path.join(dst, "STORYBOARD.md")
    text = open(sb, encoding="utf-8").read()
    text = text.replace("<SLUG>", args.slug).replace(
        "<TITLE>", args.title or args.slug)
    open(sb, "w", encoding="utf-8").write(text)
    print(f"scaffolded projects/{args.slug}/ — next: write STORYBOARD.md, "
          f"voice-input.txt, then index.html (contract: engine/ENGINE.md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
