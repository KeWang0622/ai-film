#!/usr/bin/env python3
"""Lint a shot script against the failure catalogue, before you spend anything.

    ./check_script.py --project demo

Every check here corresponds to a defect that reached a finished film. They are
cheap to run and each one has, at least once, been worth a whole batch.

Exit code is non-zero if any ERROR fires. Warnings are judgement calls.
"""

from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Dialogue pacing, per language. A single figure does not work: Latin scripts run
# at roughly 13 characters per second of speech, CJK at roughly 4.5, because a
# Chinese character carries about as much as an English word.
# Measured against restrained, paused delivery; raise for a faster register.
# Past ~0.85 of the shot the model starts rushing lines or dropping them.
CPS_CJK = 4.5
CPS_LATIN = 13.0
LINE_GAP = 0.7
DENSITY_WARN = 0.85

QUOTED = re.compile(r"「([^」]*)」|\"([^\"]*)\"|“([^”]*)”")
NUMBERED = re.compile(r"^\s*\d+\.")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def spoken_lines(dialogue: str) -> list[str]:
    out = []
    for line in dialogue.split("\n"):
        if not NUMBERED.match(line):
            continue
        for groups in QUOTED.findall(line):
            hit = next((g for g in groups if g), "")
            if hit:
                out.append(hit)
    return out


def speech_seconds(lines: list[str]) -> float:
    if not lines:
        return 0.0
    total = 0.0
    for line in lines:
        cps = CPS_LATIN if re.search(r"[A-Za-z]", line) else CPS_CJK
        total += len(line) / cps
    return total + LINE_GAP * (len(lines) - 1)


def check(film, r: Report) -> None:
    shots = film.SHOTS
    ids = [s["id"] for s in shots]

    if len(set(ids)) != len(ids):
        dupes = {i for i in ids if ids.count(i) > 1}
        r.error(f"duplicate shot ids: {', '.join(sorted(dupes))}")

    # Two projects sharing a bare id like "00-title" once applied one film's
    # transitions to another. Namespacing is the cheap fix.
    if any(re.match(r"^\d", i) for i in ids):
        r.warn("shot ids start with a digit; prefix them per project "
               "(a shared id like '00-title' can collide across projects)")

    total = sum(s["duration"] for s in shots)
    r.note(f"{len(shots)} shots / {total}s = {total // 60}:{total % 60:02d}")

    for s in shots:
        sid = s["id"]
        dur = s["duration"]
        prompt = film.build_prompt(s, _fake_refs(film))
        cast = s.get("people") or []

        if not 4 <= dur <= 30:
            r.error(f"{sid}: duration {dur}s is outside the 4-30s the endpoint accepts")

        # The music ban is not stylistic. Without it the model composes a score,
        # the score trips a copyright fingerprint, and the job is rejected AFTER
        # the video has rendered: you pay and get nothing.
        if "no music" not in prompt.lower():
            r.error(f"{sid}: no music ban in the assembled prompt")

        # A shot with no cast needs the casting block REMOVED, not a negative
        # added. "Absolutely no human figure" inside a prompt that also carries
        # casting failed three separate times — the two instructions fight and
        # casting wins.
        if not cast and "CASTING —" in prompt:
            r.error(f"{sid}: empty plate still carries a CASTING block; "
                    f"swap the block, do not add a negative")
        if not cast and film.build_image_urls(s, _fake_refs(film)):
            r.error(f"{sid}: no cast but reference images attached; "
                    f"it must route to text-to-video")
        if cast and not film.build_image_urls(s, _fake_refs(film)):
            r.error(f"{sid}: has cast but no reference images")

        # One photo per person degrades into a type — "a bald bearded older man"
        # instead of the actual person.
        for who in cast:
            value = _fake_refs(film)[film.REF_KEY[who]]
            if not isinstance(value, list) or len(value) < 2:
                r.warn(f"{sid}: '{who}' has a single reference image; "
                       f"two at different angles is markedly better")

        # Composed stillness is not a frozen frame.
        action = s["action"]
        if "MOVE:" not in action and "MOVE " not in action:
            r.warn(f"{sid}: no MOVE in the shot design; without it the camera "
                   f"either sits still or drifts with no motivation")
        static = re.search(r"MOVE[^.]*?(none whatsoever|locked off|does not move)",
                           action, re.I)
        if static and "MOVEMENT IN FRAME" not in action:
            r.warn(f"{sid}: locked-off camera and nothing stated to move in frame; "
                   f"this renders as a still photograph with a slow zoom")

        for element in ("LENS:", "FRAME:", "LIGHT:"):
            if element not in action:
                r.warn(f"{sid}: no {element[:-1]} in the shot design")
        if cast and "EYELINE" not in action:
            r.warn(f"{sid}: cast but no EYELINE; actors default to looking at the lens, "
                   f"the most anti-cinematic result available")

        lines = spoken_lines(s["dialogue"])
        secs = speech_seconds(lines)
        if lines:
            density = secs / dur
            if density > DENSITY_WARN:
                r.warn(f"{sid}: dialogue is {density:.0%} of the shot "
                       f"({len(lines)} lines ≈ {secs:.1f}s in {dur}s); "
                       f"the model will rush or drop lines")
            # Past three speakers the model loses turn-taking and has two
            # characters say the same line in unison.
            speakers = {ln.split(",")[0].split("，")[0].strip()
                        for ln in s["dialogue"].split("\n") if NUMBERED.match(ln)}
            if len(lines) > 7:
                r.warn(f"{sid}: {len(lines)} spoken lines; consider splitting the shot")
        elif "SILENT" not in s["dialogue"] and "silent" not in s["dialogue"].lower():
            # A card with nothing to say makes the model invent ambience or music,
            # which trips the same copyright filter.
            r.warn(f"{sid}: no spoken lines and no explicit silence declaration")

    fades = getattr(film, "FADES", {})
    orphans = set(fades) - set(ids)
    if orphans:
        r.error(f"FADES references shots that do not exist: {', '.join(sorted(orphans))}")
    if fades and len(ids) > 1:
        hard = sum(
            1 for a, b in zip(ids, ids[1:])
            if not fades.get(a, (0.0, 0.0))[1] and not fades.get(b, (0.0, 0.0))[0]
        )
        boundaries = len(ids) - 1
        r.note(f"{hard}/{boundaries} boundaries are hard cuts")
        if hard / boundaries < 0.4:
            r.warn(f"only {hard}/{boundaries} boundaries are hard cuts; "
                   f"dissolves everywhere read as a wedding video, not a film")

    if getattr(film, "NAME_CARDS", []):
        r.note(f"{len(film.NAME_CARDS)} burned-in cards registered")


class _Refs(dict):
    """Stand-in refs.json so the script can be linted without any uploads."""

    def __missing__(self, key):
        return [f"https://example.invalid/{key}-1.jpg",
                f"https://example.invalid/{key}-2.jpg"]


_REFS_CACHE: dict[int, _Refs] = {}


def _fake_refs(film) -> _Refs:
    key = id(film)
    if key not in _REFS_CACHE:
        real = ROOT / "refs.json"
        if real.is_file():
            import json
            _REFS_CACHE[key] = _Refs(json.loads(real.read_text()))
        else:
            _REFS_CACHE[key] = _Refs()
    return _REFS_CACHE[key]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Lint a shot script before spending.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args(argv)

    film = importlib.import_module(f"shots_{args.project}")
    r = Report()
    check(film, r)

    for n in r.notes:
        print(f"  ·  {n}")
    for w in r.warnings:
        print(f"  ⚠  {w}")
    for e in r.errors:
        print(f"  ✗  {e}")

    print()
    if r.errors:
        print(f"{len(r.errors)} error(s), {len(r.warnings)} warning(s) — fix before rendering")
        return 1
    if r.warnings and args.strict:
        print(f"{len(r.warnings)} warning(s), --strict")
        return 1
    print(f"no errors, {len(r.warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
