#!/usr/bin/env python3
"""A small, dependency-free client for the Pika media API.

generate.py uses this by default, so the pipeline runs with nothing but the
standard library. Endpoints and field names come from the published index at
https://dev.pika.art/llms.txt - read the per-model spec linked from there
rather than guessing (the ratio field is `ratio`, not `aspect_ratio`).

    from pika_client import Pika
    p = Pika()                                   # PIKA_API_KEY from env or .env.local
    url = p.upload("refs/lead-1.jpg")            # -> permanent hosted URL
    job = p.submit("bytedance/seedance-2.5/reference-to-video", payload)
    done = p.wait(job)                           # blocks; raises JobFailed
    p.download(Pika.asset_url(done), "out/01-shot.mp4")

When access fails, the status tells you why, and the three look alike from a
distance:

    401                        the key is unknown or malformed
    403 "key is not active"    the key exists but was deactivated
    caller_plan_required       the key works; the plan does not include that model

An ImportError in whatever script wraps this hides all three, which is how a
deactivated key once got diagnosed as "the model is down".
"""

from __future__ import annotations

import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = os.environ.get("PIKA_API_BASE", "https://api.dev.pika.art")
HERE = Path(__file__).resolve().parent
ENV_FILES = (HERE / ".env.local", Path.cwd() / ".env.local")

TRANSIENT = {429, 500, 502, 503, 504}


class PikaError(RuntimeError):
    """A request the server refused. `status` and `body` are kept for diagnosis."""

    def __init__(self, message: str, status: int | None = None, body: str = ""):
        super().__init__(message)
        self.status, self.body = status, body

    @property
    def diagnosis(self) -> str:
        text = self.body.lower()
        if self.status == 401:
            return "key unknown or malformed - check PIKA_API_KEY"
        if self.status == 403 and "not active" in text:
            return "key exists but has been deactivated - get a new key"
        if "caller_plan_required" in text or "not available on your current" in text:
            return "key works, but your plan does not include this model"
        if self.status == 422:
            return "payload rejected - check fields against the model spec (prompt cap is 15,000 chars)"
        return ""


class JobFailed(PikaError):
    pass


def load_key() -> str:
    key = os.environ.get("PIKA_API_KEY", "").strip()
    if key:
        return key
    for env in ENV_FILES:
        if env.is_file():
            for line in env.read_text().splitlines():
                if line.startswith("PIKA_API_KEY="):
                    return line.split("=", 1)[1].strip()
    raise SystemExit(
        "PIKA_API_KEY is not set. Export it, or put PIKA_API_KEY=... in a .env.local "
        "next to this script (chmod 600, and keep it out of git)."
    )


class Pika:
    def __init__(self, key: str | None = None, base: str = BASE):
        self.key = key or load_key()
        self.base = base.rstrip("/")

    # ------------------------------------------------------------------ http
    def _request(self, url: str, data: bytes | dict | None = None,
                 method: str | None = None, headers: dict | None = None,
                 auth: bool = True, tries: int = 5):
        hdrs = {"X-API-Key": self.key} if auth else {}
        if isinstance(data, dict):
            data = json.dumps(data).encode()
            hdrs["Content-Type"] = "application/json"
        hdrs.update(headers or {})
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        for attempt in range(tries):
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    body = resp.read()
                    # NB: `b"" in b"{["` is True. Test the first byte explicitly, or an
                    # empty 200 (a presigned PUT) gets fed to json.loads.
                    if body[:1] in (b"{", b"["):
                        return json.loads(body)
                    return body
            except urllib.error.HTTPError as exc:
                text = exc.read().decode("utf-8", "replace")
                if exc.code in TRANSIENT and attempt < tries - 1:
                    time.sleep(min(2 ** attempt, 30))
                    continue
                raise PikaError(f"HTTP {exc.code} {method or 'GET'} {url}: {text[:400]}",
                                exc.code, text) from exc
            except urllib.error.URLError:
                if attempt < tries - 1:
                    time.sleep(min(2 ** attempt, 30))
                    continue
                raise
        raise PikaError(f"retries exhausted: {url}")

    def _api(self, path: str, data=None, method: str | None = None):
        return self._request(f"{self.base}{path}", data, method)

    # ------------------------------------------------------------------ calls
    def upload(self, path: str | Path) -> str:
        """Presigned upload. Returns the permanent public URL to pass as a reference."""
        p = Path(path)
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        slot = self._api("/v1/media/uploads", {"content_type": ctype,
                                               "size_bytes": p.stat().st_size,
                                               "filename": p.name}, "POST")
        put_url = slot.get("upload_url") or slot.get("presigned_url")
        hosted = slot.get("url") or slot.get("public_url")
        if not (put_url and hosted):
            raise PikaError(f"unexpected upload slot: {json.dumps(slot)[:300]}")
        # the presigned URL carries its own auth, so the API key is not sent to storage
        self._request(put_url, p.read_bytes(), "PUT", auth=False,
                      headers={**(slot.get("headers") or {}), "Content-Type": ctype})
        return hosted

    def submit(self, api_id: str, payload: dict) -> str:
        job = self._api(f"/v1/media/{api_id}", payload, "POST")
        if not isinstance(job, dict) or not job.get("id"):
            raise PikaError(f"no job id in response: {str(job)[:300]}")
        return job["id"]

    def status(self, job_id: str) -> dict:
        return self._api(f"/v1/media/jobs/{job_id}")

    def wait(self, job_id: str, timeout_s: int = 3000, every_s: int = 10) -> dict:
        deadline, state = time.time() + timeout_s, "queued"
        while time.time() < deadline:
            job = self.status(job_id)
            state = job.get("status")
            if state == "completed":
                return job
            if state in ("failed", "cancelled"):
                err = job.get("error") or {}
                raise JobFailed(f"{job_id} {state}: {err.get('code')} {err.get('message')}",
                                None, json.dumps(job))
            time.sleep(every_s)
        raise TimeoutError(f"{job_id} still {state} after {timeout_s}s")

    def result(self, job: dict) -> dict:
        """The job's output block, falling back to /content when it is not inlined."""
        out = job.get("output")
        if out:
            return out
        return self._api(f"/v1/media/jobs/{job['id']}/content")

    def run(self, api_id: str, payload: dict, timeout_s: int = 3000) -> dict:
        """submit + wait. Returns the finished job."""
        return self.wait(self.submit(api_id, payload), timeout_s=timeout_s)

    def balance_usd(self) -> float | None:
        try:
            data = self._request(f"{self.base}/billing/balance", tries=1)
        except Exception:
            return None
        for k in ("balance_usd", "usd", "balance"):
            if isinstance(data, dict) and isinstance(data.get(k), (int, float)):
                return float(data[k])
        return None

    @staticmethod
    def asset_url(job: dict) -> str | None:
        out = job.get("output") or {}
        for kind in ("video", "audio", "image"):
            if isinstance(out.get(kind), dict) and out[kind].get("url"):
                return out[kind]["url"]
        return out.get("url")

    @staticmethod
    def charge_usd(job: dict) -> float:
        return (job.get("billing") or {}).get("charge_micro_usd", 0) / 1e6

    def download(self, url: str, dest: str | Path) -> Path:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        body = self._request(url, auth=False)
        dest.write_bytes(body if isinstance(body, bytes) else json.dumps(body).encode())
        return dest


if __name__ == "__main__":
    import sys
    # `./pika_client.py upload refs/*.jpg > refs.json`
    # Files are grouped by the name before the first "-": driver-1.jpg and
    # driver-2.jpg become {"driver": [url, url]}, which is the refs.json shape.
    if len(sys.argv) > 2 and sys.argv[1] == "upload":
        client, refs = Pika(), {}
        for name in sorted(sys.argv[2:]):
            refs.setdefault(Path(name).stem.split("-")[0], []).append(client.upload(name))
            print(f"uploaded {name}", file=sys.stderr)
        print(json.dumps(refs, indent=2))
    else:
        print(__doc__)
