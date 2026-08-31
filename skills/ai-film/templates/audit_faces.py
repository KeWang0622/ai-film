#!/usr/bin/env python3
"""Crop faces out of every rendered shot and put them beside the references.

    ./audit_faces.py --project demo
    ./audit_faces.py --project demo --shots 06,11

A wide frame is not verification. Three separate defects have shipped past a
"verified" wide look:

  * the focal plane went to a foreground prop and the face went soft
  * a mid-shot face was too small and drifted into a different person
  * two same-gender leads wore each other's costume for an entire film —
    the hardest one to catch, because both faces *are* present

So the check has to crop, scale up, and sit next to the reference photograph.
Judge on hardware that exists in the photo (glasses shape, a specific chain,
a carried object), never on face shape: profile and low light lie.

Exit code 0 means the sheets were written. It does not mean they passed.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

GRID = 3  # slice each frame into thirds so we do not have to guess where the face is


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def reference_strip(film, refs: dict, out: Path, cache: Path) -> list[str]:
    """Download one reference per character and stack them into a strip."""
    cache.mkdir(exist_ok=True)
    paths, order = [], []
    for who, key in film.REF_KEY.items():
        value = refs[key]
        url = value[0] if isinstance(value, list) else value
        dst = cache / f"{key}.jpg"
        if not dst.is_file():
            run(["curl", "-sfL", "-o", str(dst), url])
        paths.append(dst)
        order.append(who)
    inputs = [x for p in paths for x in ("-i", str(p))]
    chain = "".join(f"[{i}]scale=-2:420[s{i}];" for i in range(len(paths)))
    chain += "".join(f"[s{i}]" for i in range(len(paths))) + f"hstack=inputs={len(paths)}"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", chain, str(out)])
    return order


def contact_sheet(clip: Path, dst: Path, at: float) -> None:
    parts = []
    for i in range(GRID):
        part = dst.with_name(f".{dst.stem}-{i}.png")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(at), "-i", str(clip),
             "-frames:v", "1", "-vf",
             f"crop=iw/{GRID}:ih*0.7:iw*{i}/{GRID}:0,scale=460:-2", str(part)])
        parts.append(part)
    inputs = [x for p in parts for x in ("-i", str(p))]
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
         "".join(f"[{i}]" for i in range(GRID)) + f"hstack=inputs={GRID}", str(dst)])
    for part in parts:
        part.unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build face-audit contact sheets.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--shots", default="", help="comma-separated shot id fragments")
    args = parser.parse_args(argv)

    film = importlib.import_module(f"shots_{args.project}")
    refs = json.loads((ROOT / "refs.json").read_text())
    clips = ROOT / f"out_{args.project}"
    outdir = ROOT / f"audit_{args.project}"
    outdir.mkdir(exist_ok=True)
    wanted = {x.strip() for x in args.shots.split(",") if x.strip()}

    strip = outdir / "_references.png"
    order = reference_strip(film, refs, strip, ROOT / ".refcache")
    print(f"references ({', '.join(order)}) -> {strip.name}")

    for shot in film.SHOTS:
        if not shot.get("people"):
            continue
        sid = shot["id"]
        if wanted and not any(w in sid for w in wanted):
            continue
        clip = clips / f"{sid}.mp4"
        if not clip.is_file():
            print(f"  missing {sid}", file=sys.stderr)
            continue
        dst = outdir / f"{sid}.png"
        contact_sheet(clip, dst, at=shot["duration"] * 0.6)
        print(f"  {sid:24s} [{'+'.join(shot['people'])}] -> {dst.name}")

    print(f"\nNow look at {outdir}/ by hand:")
    print("  1. put each face beside the reference strip")
    print("  2. judge on glasses shape / hardware, never on face shape")
    print("  3. confirm WHICH person is wearing WHICH costume")
    print("  4. confirm the face, not a prop, is the focal plane")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
