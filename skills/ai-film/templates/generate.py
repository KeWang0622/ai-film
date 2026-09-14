#!/usr/bin/env python3
"""Render every shot of a project. This is the paid, slow half of the pipeline.

    ./generate.py --project demo --dry-run     print payloads + cost, spend nothing
    ./generate.py --project demo               render all shots
    ./generate.py --project demo --shots 3,7   re-render specific shots
    ./generate.py --project demo --shots 05-the-door

A project is a module `shots_<name>.py` next to this file. See
`shots_template.py` for the contract. Output lands in `out_<name>/`.

Reference images are read from `refs.json` — a flat map of key -> URL or
[URL, ...]. The project module decides which keys each shot needs. Upload local
photos and print that map with:

    ./pika_client.py upload refs/*.jpg > refs.json

Auth: PIKA_API_KEY in the environment, or in a .env.local next to this script.
Transport is `pika_client.py` - standard library only, nothing to install.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pika_client import JobFailed, Pika, PikaError  # noqa: E402  (stdlib only)

# Shots with cast go to reference-to-video. Shots with no cast MUST go to
# text-to-video: the reference endpoint requires at least one image and returns
# 422 without one, and satisfying it with an unrelated image drags that person
# into a plate that is supposed to be empty.
API_REFERENCE = "bytedance/seedance-2.5/reference-to-video"
API_TEXT = "bytedance/seedance-2.5/text-to-video"

REFS_FILE = ROOT / "refs.json"

# Measured per-second charge at 1080p, reference- and text-to-video alike,
# from job billing records (consistent to 0.2% across 60+ renders). Reason about
# spend from billing, never from list prices — a naive estimate once read 4x high.
EST_USD_PER_SECOND = 0.46

# The server caps concurrent jobs (20). Exceeding it also makes *uploads* fail
# with 429, which is a confusing way to discover the limit. Six is comfortable.
DEFAULT_CONCURRENCY = 6

# Seedance rejects prompts over 15,000 characters with a 422 - and in a batch,
# that shot simply never renders. check_script.py errors on it before you spend.
PROMPT_LIMIT = 15000


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


def render(client: Pika, film, shot: dict, refs: dict, out_dir: Path,
           attempts: int = 2) -> tuple[Path | None, float]:
    label = shot["id"]
    dest = out_dir / f"{label}.mp4"
    # Resumable: a re-run never pays twice. To re-render a take, move it aside
    # (keep it - the rejected take is the evidence for why you changed the prompt).
    if dest.is_file() and dest.stat().st_size > 100_000:
        print(f"  [{label}] exists, skipped", flush=True)
        return dest, 0.0

    payload = build_payload(film, shot, refs)
    api = API_REFERENCE if "image_urls" in payload else API_TEXT
    for attempt in range(1, attempts + 1):
        try:
            job_id = client.submit(api, payload)
            print(f"  [{label}] submitted {job_id}", flush=True)
            job = client.wait(job_id, timeout_s=3000, every_s=10)
        except (PikaError, TimeoutError) as exc:
            hint = getattr(exc, "diagnosis", "")
            print(f"  [{label}] attempt {attempt} failed: {exc}"
                  + (f"\n  [{label}] -> {hint}" if hint else ""), file=sys.stderr, flush=True)
            # Access and payload errors will not fix themselves; do not queue again.
            if isinstance(exc, PikaError) and not isinstance(exc, JobFailed) and hint:
                return None, 0.0
            # `provider_timeout` is a ~20-minute server ceiling driven by queue load,
            # not shot complexity, and it bills nothing. Retry unchanged.
            if attempt < attempts:
                print(f"  [{label}] retrying unchanged…", file=sys.stderr, flush=True)
                continue
            return None, 0.0

        url = Pika.asset_url(job)
        if not url:
            print(f"  [{label}] no asset URL: {json.dumps(job)[:300]}", file=sys.stderr)
            return None, 0.0
        client.download(url, dest)
        cost = Pika.charge_usd(job)
        print(f"  [{label}] saved {dest.name} ({dest.stat().st_size / 1_048_576:.1f} MB, "
              f"${cost:.2f})", flush=True)
        return dest, cost
    return None, 0.0


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

    too_long = [(s["id"], len(build_payload(film, s, refs)["prompt"])) for s in shots]
    too_long = [(i, n) for i, n in too_long if n > PROMPT_LIMIT]
    if too_long:
        for sid, n in too_long:
            print(f"  {sid}: prompt is {n} chars (limit {PROMPT_LIMIT}) - it would 422",
                  file=sys.stderr)
        return 2

    client = Pika()
    out_dir.mkdir(exist_ok=True)
    balance = client.balance_usd()
    print(f"model      : {API_REFERENCE}")
    print(f"config     : {len(shots)} shots / {seconds}s @ "
          f"{getattr(film, 'RESOLUTION', '1080p')} {getattr(film, 'RATIO', '21:9')}")
    print(f"estimate   : ≈ ${seconds * EST_USD_PER_SECOND:.2f}")
    if balance is not None:
        print(f"balance    : ${balance:.2f}")
    if not args.yes and input("proceed? [y/N] ").strip().lower() not in {"y", "yes"}:
        return 1

    started = datetime.now(timezone.utc)
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(lambda s: render(client, film, s, refs, out_dir), shots))

    paths = [p for p, _ in results]
    spent = sum(c for _, c in results)
    done = [p for p in paths if p]
    elapsed = (datetime.now(timezone.utc) - started).seconds
    print(f"\n{len(done)}/{len(shots)} rendered in {elapsed // 60}m{elapsed % 60}s, "
          f"spent ${spent:.2f}")
    if len(done) != len(shots):
        missing = [s["id"] for s, p in zip(shots, paths) if not p]
        print(f"retry: --shots {','.join(missing)}", file=sys.stderr)
    return 0 if len(done) == len(shots) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
