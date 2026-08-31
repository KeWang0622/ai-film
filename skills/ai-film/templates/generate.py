#!/usr/bin/env python3
"""Render every shot of a project. This is the paid, slow half of the pipeline.

    ./generate.py --project demo --dry-run     print payloads + cost, spend nothing
    ./generate.py --project demo               render all shots
    ./generate.py --project demo --shots 3,7   re-render specific shots
    ./generate.py --project demo --shots 05-the-door

A project is a module `shots_<name>.py` next to this file. See
`shots_template.py` for the contract. Output lands in `out_<name>/`.

Reference images are read from `refs.json` — a flat map of key -> URL or
[URL, ...]. The project module decides which keys each shot needs.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

_sdk = os.environ.get("AI_FILM_SDK")
if _sdk:
    sys.path.insert(0, _sdk)

# Imported defensively so --dry-run works with nothing installed: reading the
# assembled prompts is free, and is the first thing anyone should do.
try:
    from pika_api import JobFailed, PikaAPIError, PikaClient, load_config
    from pika_api.assets import download, find_asset_url
    from pika_api.config import ConfigError
except ImportError:  # only --dry-run is available without the SDK
    JobFailed = PikaAPIError = ConfigError = Exception
    PikaClient = load_config = download = find_asset_url = None

# Shots with cast go to reference-to-video. Shots with no cast MUST go to
# text-to-video: the reference endpoint requires at least one image and returns
# 422 without one, and satisfying it with an unrelated image drags that person
# into a plate that is supposed to be empty.
API_REFERENCE = "bytedance/seedance-2.5/reference-to-video"
API_TEXT = "bytedance/seedance-2.5/text-to-video"

REFS_FILE = ROOT / "refs.json"

# Conservative per-second estimate for 1080p. Reason about real spend from the
# billing endpoint, not from list prices — a naive estimate once read 4x high.
EST_USD_PER_SECOND = 0.45

# The server caps concurrent jobs. Exceeding it also makes *uploads* fail with
# 429, which is a confusing way to discover the limit.
DEFAULT_CONCURRENCY = 3


def load_project(name: str):
    try:
        return importlib.import_module(f"shots_{name}")
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"No shots_{name}.py next to this script. Copy shots_template.py to "
            f"shots_{name}.py and edit it."
        ) from exc


class _Placeholder(dict):
    """Stands in for refs.json so --dry-run works before anything is uploaded."""

    def __missing__(self, key):
        return [f"https://example.invalid/{key}-1.jpg",
                f"https://example.invalid/{key}-2.jpg"]


def load_refs(required: bool = True) -> dict:
    if REFS_FILE.is_file():
        return json.loads(REFS_FILE.read_text())
    if required:
        raise SystemExit(
            f"missing {REFS_FILE} — a map of ref key -> image URL (or list of URLs). "
            f"See refs.example.json."
        )
    return _Placeholder()


def build_payload(film, shot: dict, refs: dict) -> dict:
    urls = film.build_image_urls(shot, refs)
    payload: dict[str, object] = {
        "prompt": film.build_prompt(shot, refs),
        "duration": shot["duration"],
        "resolution": getattr(film, "RESOLUTION", "1080p"),
        "ratio": getattr(film, "RATIO", "21:9"),
        "generate_audio": getattr(film, "GENERATE_AUDIO", True),
        "bitrate_mode": getattr(film, "BITRATE_MODE", "high"),
    }
    if urls:
        payload["image_urls"] = urls
    return payload


def render(client: PikaClient, film, shot: dict, refs: dict, out_dir: Path,
           attempts: int = 2) -> Path | None:
    label = shot["id"]
    payload = build_payload(film, shot, refs)
    api = API_REFERENCE if "image_urls" in payload else API_TEXT

    for attempt in range(1, attempts + 1):
        try:
            job = client.submit(api, payload)
            print(f"  [{label}] submitted {job.request_id}", flush=True)
            finished = client.wait(job.request_id, poll_interval_s=10.0, max_wait_s=3000.0)
            result = finished.raw.get("output") or client.content(job.request_id)
        except (PikaAPIError, JobFailed, TimeoutError) as exc:
            # `provider_timeout: exceeded max lifetime` is a ~20-minute server
            # ceiling driven by queue load, not by shot complexity. The same
            # prompt usually passes on a retry. Content-moderation failures will
            # not, but the only cost of finding out is one more place in the queue.
            print(f"  [{label}] attempt {attempt} failed: {exc}", file=sys.stderr, flush=True)
            if attempt < attempts:
                print(f"  [{label}] retrying unchanged…", file=sys.stderr, flush=True)
                continue
            return None

        url = find_asset_url(result)
        if not url:
            print(f"  [{label}] no asset URL: {json.dumps(result)[:300]}", file=sys.stderr)
            return None
        path = download(url, out_dir / f"{label}.mp4")
        print(f"  [{label}] saved {path.name} "
              f"({path.stat().st_size / 1_048_576:.1f} MB)", flush=True)
        return path
    return None


def select(film, wanted: str) -> list[dict]:
    """Accept either 1-based indices or shot ids.

    Indices alone are too easy to get wrong: inserting one scene shifts every
    number after it.
    """
    shots = film.SHOTS
    if not wanted:
        return shots
    keys = {x.strip() for x in wanted.split(",") if x.strip()}
    chosen = [s for i, s in enumerate(shots, 1) if str(i) in keys or s["id"] in keys]
    known = {str(i) for i in range(1, len(shots) + 1)} | {s["id"] for s in shots}
    unknown = keys - known
    if unknown:
        raise SystemExit(f"unknown shots: {', '.join(sorted(unknown))}")
    return chosen


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Render a film project's shots.")
    parser.add_argument("--project", required=True, help="loads shots_<name>.py")
    parser.add_argument("--shots", default="", help="comma-separated indices or shot ids")
    parser.add_argument("--dry-run", action="store_true", help="print payloads, spend nothing")
    parser.add_argument("--yes", action="store_true", help="skip the cost confirmation")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    args = parser.parse_args(argv)

    film = load_project(args.project)
    refs = load_refs(required=not args.dry_run)
    shots = select(film, args.shots)
    out_dir = ROOT / f"out_{args.project}"
    seconds = sum(s["duration"] for s in shots)

    if args.dry_run:
        for shot in shots:
            print(f"===== {shot['id']}  ({shot['duration']}s)")
            print(json.dumps(build_payload(film, shot, refs), ensure_ascii=False, indent=2))
        print(f"\n{len(shots)} shots / {seconds}s "
              f"≈ ${seconds * EST_USD_PER_SECOND:.2f}")
        return 0

    if PikaClient is None:
        print("The generation SDK is not importable. Point AI_FILM_SDK at it, or use "
              "--dry-run to inspect prompts without it.", file=sys.stderr)
        return 2
    try:
        client = PikaClient(load_config())
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 2

    out_dir.mkdir(exist_ok=True)
    print(f"model      : {API_REFERENCE}")
    print(f"config     : {len(shots)} shots / {seconds}s @ "
          f"{getattr(film, 'RESOLUTION', '1080p')} {getattr(film, 'RATIO', '21:9')}")
    print(f"estimate   : ≈ ${seconds * EST_USD_PER_SECOND:.2f}")
    print(f"balance    : ${client.balance_usd():.2f}")
    if not args.yes and input("proceed? [y/N] ").strip().lower() not in {"y", "yes"}:
        return 1

    started = datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        paths = list(pool.map(lambda s: render(client, film, s, refs, out_dir), shots))

    done = [p for p in paths if p]
    elapsed = (datetime.now(timezone.utc) - started).seconds
    print(f"\n{len(done)}/{len(shots)} rendered in {elapsed // 60}m{elapsed % 60}s")
    if len(done) != len(shots):
        missing = [s["id"] for s, p in zip(shots, paths) if not p]
        print(f"retry: --shots {','.join(missing)}", file=sys.stderr)
    return 0 if len(done) == len(shots) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
