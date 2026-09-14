#!/usr/bin/env python3
"""Measure a finished film instead of looking at it. Free.

    ./verify_film.py --project demo --cut demo-MASTER.mp4

Every check here is a defect that shipped past a "looks fine" glance:

  runtime   cut duration vs the sum of the real clip durations. Silent truncation
            exits 0 in this pipeline; clips also render ~0.06s longer than asked.
  colour    MONOCHROME projects: 95th-percentile chroma must be ~0. Use the
            percentile, never the mean - a lamp and a blue door vanish into the
            mean of a mostly-neutral frame. Colour projects: flags shots that came
            back drained, which is the opposite failure.
  music     the video model sometimes scores a shot despite the ban. Music
            concentrates energy in a few spectral bins; ambience does not.
  banding   long flat runs along a gradient. Skips dips to black, which are flat
            by definition and once reported a 1,663-pixel "band".
  heads     speech energy at the head of every clip after a dip, so you know a
            line starts at 0.00s before any transition is allowed near it.

A measurement that cannot be computed is a FAILURE, not a pass. An earlier probe
returned -1 for every clip because its parser matched nothing, and the table
read like a clean bill of health.
"""
from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    sys.exit("verify_film.py needs numpy (pip install numpy)")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def probe_duration(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout
    return float(out.strip())


def frame_yuv(p: Path, t: float, w: int = 480) -> np.ndarray | None:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(p),
                          "-frames:v", "1", "-vf", f"scale={w}:-2", "-pix_fmt", "yuv444p",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    if not raw or len(raw) % 3:
        return None
    px = len(raw) // 3
    h = px // w
    return np.frombuffer(raw, np.uint8)[: 3 * w * h].reshape(3, h, w)


def chroma_p95(p: Path, samples: int = 12) -> float | None:
    d, worst = probe_duration(p), None
    for k in range(samples):
        f = frame_yuv(p, d * (k + 0.5) / samples)
        if f is None:
            continue
        c = np.hypot(f[1].astype(np.int16) - 128, f[2].astype(np.int16) - 128)
        v = float(np.percentile(c, 95))
        worst = v if worst is None else max(worst, v)
    return worst


def audio(p: Path, start: float = 0.0, dur: float | None = None, sr: int = 16000):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", str(p)]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    raw = subprocess.run(cmd + ["-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768, sr


def tonal_share(p: Path) -> float | None:
    x, sr = audio(p, sr=22050)
    if len(x) < sr:
        return None
    s = np.abs(np.fft.rfft(x * np.hanning(len(x)))) + 1e-12
    f = np.fft.rfftfreq(len(x), 1 / sr)
    band = s[(f > 60) & (f < 2000)]
    return float(np.sort(band)[-12:].sum() / band.sum())


def speech_db(p: Path, start: float, dur: float) -> float | None:
    x, sr = audio(p, start, dur)
    if len(x) < 400:
        return None
    s = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1 / sr)
    return float(20 * np.log10(max(np.sqrt((s[(f >= 300) & (f <= 3400)] ** 2).mean()), 1e-9)))


def longest_flat_run(p: Path, samples: int = 24) -> int | None:
    d, runs = probe_duration(p), []
    for k in range(samples):
        f = frame_yuv(p, d * (0.05 + 0.9 * (k + 0.5) / samples), w=960)
        if f is None or f[0].mean() < 12:        # a dip to black is flat by definition
            continue
        row = f[0][f.shape[1] // 2].astype(np.int16)
        flat = np.diff(row) == 0
        best = cur = 0
        for v in flat:
            cur = cur + 1 if v else 0
            best = max(best, cur)
        runs.append(best)
    return int(np.median(runs)) if runs else None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Measure a finished film.")
    ap.add_argument("--project", required=True)
    ap.add_argument("--cut", type=Path, required=True)
    a = ap.parse_args(argv)
    film = importlib.import_module(f"shots_{a.project}")
    clips_dir = ROOT / f"out_{a.project}"
    mono = bool(getattr(film, "MONOCHROME", False))
    fades = getattr(film, "FADES", {})
    fails = 0

    def report(ok: bool | None, label: str, detail: str) -> None:
        nonlocal fails
        mark = "PASS" if ok else ("FAIL" if ok is False else "????")
        if ok is not True:
            fails += 1
        print(f"  [{mark}] {label:10s} {detail}")

    clips = [(s["id"], clips_dir / f"{s['id']}.mp4") for s in film.SHOTS]
    missing = [i for i, p in clips if not p.is_file()]
    report(not missing, "clips", f"{len(clips) - len(missing)}/{len(clips)} present"
           + (f"; missing {', '.join(missing)}" if missing else ""))
    clips = [(i, p) for i, p in clips if p.is_file()]

    expected = sum(probe_duration(p) for _, p in clips)
    got = probe_duration(a.cut)
    report(abs(got - expected) < 0.15, "runtime",
           f"cut {got:.2f}s vs clips {expected:.2f}s (delta {got - expected:+.2f}s)")

    c = chroma_p95(a.cut, 40)
    if c is None:
        report(None, "colour", "could not read frames")
    elif mono:
        report(c < 4, "colour", f"monochrome film: worst p95 chroma {c:.2f} (want < 4)")
    else:
        drained = [i for i, p in clips if (v := chroma_p95(p, 4)) is not None and v < 8
                   and "card" not in i and "title" not in i]
        report(not drained, "colour", "colour film: " +
               (f"drained shots {', '.join(drained)}" if drained else "no shot came back drained"))

    leaks, unread = [], []
    for i, p in clips:
        share = tonal_share(p)
        if share is None:
            unread.append(i)
        elif share > 0.25:
            leaks.append(f"{i} ({share:.0%})")
    report(False if leaks else (None if unread else True), "music",
           f"tonal energy >25% in: {', '.join(leaks)}" if leaks else
           (f"unreadable: {', '.join(unread)}" if unread else "no model-composed music in any clip"))

    run = longest_flat_run(a.cut)
    report(None if run is None else run <= 60, "banding",
           "no readable frames" if run is None else f"median longest flat run {run}px (want <= 60)")

    ids = [i for i, _ in clips]
    print("\n  heads after a dip (speech dB in the first 0.35s; picture-only dips make these safe):")
    for n, (i, p) in enumerate(clips):
        prev = ids[n - 1] if n else None
        if n == 0 or fades.get(i, (0, 0))[0] or (prev and fades.get(prev, (0, 0))[1]):
            db = speech_db(p, 0.0, 0.35)
            flag = "  <- a line starts here; never fade the audio" if db is not None and db > 0 else ""
            print(f"    {i:28s} {'unreadable' if db is None else f'{db:6.1f} dB'}{flag}")

    head = a.cut.read_bytes()[:64]
    report(b"moov" in head, "faststart", "moov atom at the head" if b"moov" in head
           else "moov at the tail - browsers will download the whole file first")
    print(f"\n{'ALL CHECKS PASS' if not fails else f'{fails} check(s) failed or unreadable'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
