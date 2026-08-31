# Delivery: encoding, hosting, sending

The last mile has its own failure modes, and they are the ones the viewer actually
experiences.

---

## faststart, always

**Symptom:** the link opens and nothing renders. The file is fine; the CDN is fine.

**Cause:** `moov` is written at the end of the file, so a browser must download all
of it before it can show a frame. A 48 MB film looks broken for however long the
download takes.

**Why it survives testing:** local players (`ffplay`, VLC, QuickTime, Finder
preview) do not care where `moov` is. It only appears over HTTP, which is exactly
where the user sees it.

```bash
# remux only — no re-encode, seconds
ffmpeg -i in.mp4 -c copy -movflags +faststart out.mp4
```

Verify, don't assume:

```python
# top-level atom order must be ftyp → moov → … → mdat
import struct
d = open(path,'rb'); pos=0; order=[]
while len(order) < 6:
    d.seek(pos); h = d.read(8)
    if len(h) < 8: break
    size = struct.unpack('>I', h[:4])[0]; order.append(h[4:8].decode('latin1'))
    if size == 1: size = struct.unpack('>Q', d.read(8))[0]
    if size == 0: break
    pos += size
assert order.index('moov') < order.index('mdat')
```

Put `+faststart` in the share-encode step permanently.

---

## Two encodes, always

| Encode | Settings | For |
|---|---|---|
| Master | `-preset slow -crf 16 -c:a aac -b:a 192k` | archive, further work |
| Share | `-preset slow -crf 23 -c:a aac -b:a 160k -movflags +faststart` | links, email |

A 195 s 21:9 1080p film: master ~110 MB, share ~48 MB. The share encode is what
gets uploaded — the upload endpoint rejects large files with `HTTP 413 file too
large`.

---

## Hosting and links

```python
from pika_api.uploads import upload_file
url = upload_file(PikaClient(load_config()), Path("share.mp4"))
# → https://cdn.pika.art/... , publicly readable, no auth, supports range requests
```

- Verify with `curl -s -o /dev/null -w "%{http_code}" -r 0-1000 <url>` → expect
  **206** (range supported = seekable playback).
- `HTTP 429 concurrency limit exceeded: 20 video job(s) already in flight` — the
  *upload* endpoint shares the generation concurrency pool. After a big batch of
  reruns, uploads fail until slots free. Retry with a delay.
- Keep a `links.json` so a re-upload does not lose the earlier URLs.

---

## Email

The Gmail action takes attachments only as objects already in the connector's
storage (an `s3key`), not local paths, and Gmail caps messages at ~25 MB. **Send
the CDN link, not the file.**

A good delivery email contains:

- the link, and the local master path with its size
- specs: duration, resolution, shot count, language, subtitles y/n, score y/n
- what the film is doing structurally — the object's three beats, the promise, the
  rhyming shots — so the viewer knows what to watch for
- **known defects, stated plainly**, including anything deliberately not fixed and
  why
- what changed since the last cut, if it is a revision

---

## Name cards and other global state

A helper returning name cards fell through to a default set for any unregistered
project, and burned one film's character names into two unrelated films — silently,
for days.

**Make global overlays opt-in by explicit whitelist:**

```python
def _name_cards(project: str):
    if project == "en": ...
    # films with no registered cards get NOTHING
    if project in ("sad", "happy"):
        return NAME_CARDS
    return []
```

The same shape of bug applies to any dict keyed by shot id across projects (fades,
subtitle styles): two films can share a shot id like `00-title` or `09-the-door`.
Namespace them or key by `(project, shot_id)`.
