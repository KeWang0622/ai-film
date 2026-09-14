#!/usr/bin/env python3
"""Turn a finished cut into delivery tiers. Free, fast, re-runnable.

    ./deliver.py cut.mp4                 -> NAME-MASTER.mp4, NAME-full.mp4, NAME-share.mp4
    ./deliver.py cut.mp4 --share-mb 30   fit the share copy under a size cap

    MASTER   video stream-copied (stays first generation); audio normalised
    full     full resolution, CRF 19        what people should actually watch
    share    720p, CRF 23, stepped up until it fits --share-mb

Two rules this file exists to enforce:

1. Loudness normalisation must be TWO-PASS LINEAR. Single-pass `loudnorm` is a
   dynamic compressor: it lifted a deliberately silent title card by ~25 dB into
   audible hiss. Measure first, then apply one constant gain - silence stays
   silent and dialogue comes forward.

2. `-tune grain` on anything with film grain (and every monochrome film). By
   default x264 treats grain as noise and smooths it, which kills the texture
   and brings back the banding the grain was hiding.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TARGET = "I=-16:TP=-1.5:LRA=11"


def _run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed: {' '.join(cmd[:8])} ...\n{r.stderr[-1500:]}")
    return r.stderr


def loudnorm_linear(src: Path, dst: Path, pre: str = "", video: str = "copy",
                    extra: list[str] | None = None) -> dict:
    """Two-pass linear loudnorm. `pre` filters run in BOTH passes so the
    measurement describes the audio that is actually normalised."""
    chain = f"{pre}," if pre else ""
    log = _run(["ffmpeg", "-hide_banner", "-i", str(src), "-af",
                f"{chain}loudnorm={TARGET}:print_format=json", "-f", "null", "-"])
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", log, re.S).group(0))
    measured = (f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                f"offset={m['target_offset']}:linear=true")
    vcodec = ["-c:v", "copy"] if video == "copy" else video.split()
    _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
          "-af", f"{chain}loudnorm={TARGET}:{measured}", *vcodec,
          "-c:a", "aac", "-b:a", "256k", *(extra or []), "-movflags", "+faststart", str(dst)])
    return m


def encode(src: Path, dst: Path, crf: int, height: int | None, grain: bool, abr: str) -> Path:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p"]
    if grain:
        cmd += ["-tune", "grain"]
    if height:
        # never upscale: a share copy of a 480p cut must stay 480p
        cmd += ["-vf", f"scale=-2:'min({height},ih)'"]
    _run(cmd + ["-c:a", "aac", "-b:a", abr, "-movflags", "+faststart", str(dst)])
    return dst


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build delivery tiers from a finished cut.")
    ap.add_argument("cut", type=Path)
    ap.add_argument("--name", help="output stem (default: input stem)")
    ap.add_argument("--no-grain", action="store_true", help="omit -tune grain (clean digital look)")
    ap.add_argument("--share-mb", type=float, default=0, help="size cap for the share copy")
    a = ap.parse_args(argv)

    stem = a.name or a.cut.stem.replace("-raw", "").replace("-final", "")
    out = a.cut.parent
    grain = not a.no_grain
    master = out / f"{stem}-MASTER.mp4"
    m = loudnorm_linear(a.cut, master)
    print(f"MASTER  {master.name}  (measured {m['input_i']} LUFS -> -16, linear)")
    full = encode(master, out / f"{stem}-full.mp4", 19, None, grain, "192k")
    print(f"full    {full.name}")

    crf, share = 23, out / f"{stem}-share.mp4"
    while True:
        encode(master, share, crf, 720, grain, "128k")
        mb = share.stat().st_size / 1_048_576
        if not a.share_mb or mb <= a.share_mb or crf >= 32:
            break
        crf += 2
    print(f"share   {share.name}  {mb:.1f} MB at CRF {crf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
