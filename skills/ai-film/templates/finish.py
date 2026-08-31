#!/usr/bin/env python3
"""Post-production: concat -> subtitles -> score -> mix -> deliverable.

    ./finish.py --project demo                 full pass
    ./finish.py --project demo --no-music      concat + denoise only
    ./finish.py --project demo --no-subs       skip transcription/subtitles
    ./finish.py --project demo --srt cues.srt  reuse an existing SRT

Everything here is free and re-runnable. Never regenerate a shot to fix
something that lives in post.

The score is generated as a separate stem and ducked under the dialogue rather
than asking the video model for music: model-composed score trips copyright
moderation *after* the render is paid for, and its level cannot be controlled.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# The generation SDK lives outside this repo. Point AI_FILM_SDK at it, or drop
# this file next to the SDK package. Post-production works without it; only
# score generation and transcription need the network.
_sdk = os.environ.get("AI_FILM_SDK")
if _sdk:
    sys.path.insert(0, _sdk)
try:
    from pika_api import PikaClient, load_config
    from pika_api.assets import download, find_asset_url
except ImportError:  # post-only runs do not need the SDK
    PikaClient = load_config = download = find_asset_url = None  # type: ignore


# ── Project loading ─────────────────────────────────────────────────────────
# A project is a module `shots_<name>.py` on the path. Required: SHOTS.
# Optional, with sane fallbacks: FADES, NAME_CARDS, MUSIC_PROMPT, LANG.

_CACHE: dict[str, object] = {}


def project_module(project: str):
    if project not in _CACHE:
        try:
            _CACHE[project] = importlib.import_module(f"shots_{project}")
        except ModuleNotFoundError as exc:
            raise SystemExit(
                f"No shots_{project}.py on the path. Copy templates/shots_template.py "
                f"to shots_{project}.py and edit it."
            ) from exc
    return _CACHE[project]


def _attr(project: str, name: str, default):
    return getattr(project_module(project), name, default)


# Fonts. The model cannot render legible on-screen text at a controllable size,
# so every card and subtitle is burned in here instead.
FONT_CJK = os.environ.get(
    "AI_FILM_FONT_CJK", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
)
FONT_LATIN = os.environ.get(
    "AI_FILM_FONT_LATIN", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
)


def _font(project: str) -> str:
    return FONT_LATIN if _attr(project, "LANG", "zh") == "en" else FONT_CJK


def _font_name(project: str) -> str:
    return "DejaVu Sans" if _attr(project, "LANG", "zh") == "en" else "Droid Sans Fallback"


def _name_cards(project: str):
    """Burned-in cards are strictly opt-in.

    A helper that fell through to a default set once burned one film's character
    names into two unrelated films, silently, for days. Projects that register
    nothing get nothing.
    """
    return _attr(project, "NAME_CARDS", [])


def name_card_filter(project: str) -> str:
    """One drawtext filter per card, each with a 0.5s fade in and out."""
    parts = []
    for text, start, dur, xf, yf, size in _name_cards(project):
        fade = (
            f"if(lt(t,{start}),0,"
            f"if(lt(t,{start + 0.5}),(t-{start})/0.5,"
            f"if(lt(t,{start + dur - 0.5}),1,"
            f"if(lt(t,{start + dur}),({start + dur}-t)/0.5,0))))"
        )
        parts.append(
            f"drawtext=fontfile={_font(project)}:text='{text}':"
            f"fontsize={size}:fontcolor=white:alpha='{fade}':"
            f"x=w*{xf}-text_w/2:y=h*{yf}:"
            f"borderw=3:bordercolor=black@0.5:"
            f"shadowcolor=black@0.7:shadowx=3:shadowy=3"
        )
    return ",".join(parts)


# Transitions are designed per boundary. Cinema is ~95% hard cuts; dissolves
# everywhere read as a wedding video, not a film.
#
# Use a dip to black, not a cross-dissolve: a dissolve says "at the same time,
# related", while black says "time passed".
#
# CRITICAL: the fade filter cannot produce a mid-film dip on the master.
# `fade=t=in:st=108` does not mean "fade in at 108s" — it renders every frame
# BEFORE 108s black. Two such filters once turned an 86 MB master into 3.2 MB.
# Fades must be applied to each clip before concatenation, which also keeps the
# runtime exact.
def fades(project: str) -> dict[str, tuple[float, float]]:
    """Per-shot (fade_in, fade_out), keyed by shot id, from the project module.

    Cinema is ~95% hard cuts. Dip to black only for a time ellipsis or an act
    boundary; a transition on a disaster telegraphs it and kills the impact.

    Fades are applied INSIDE each clip before concatenation, never on the
    master: `fade=t=in:st=108` does not mean "fade in at 108s", it renders every
    frame before 108s black. Doing it per-clip also keeps the runtime exact.
    """
    return _attr(project, "FADES", {})




# Frame size. The ASS PlayRes must match it exactly, or libass rescales
# everything and FontSize / MarginV stop being pixel values.
VIDEO_W, VIDEO_H = 2206, 946

# Cinema defaults: cap height ~4.5% of frame height, bottom margin ~5%.
SUB_FONTSIZE = 50
SUB_MARGIN_V = 46


def srt_to_ass(srt: Path, project: str) -> Path:
    """Convert SRT to ASS with a real PlayRes header.

    Do not use the subtitles filter's `force_style`: on that path PlayResY
    defaults to 288, so libass scales FontSize and MarginV by ~3.28x on a
    946-tall video. The text renders huge and floats well above the bottom edge.
    Writing PlayRes explicitly makes FontSize and MarginV true pixels.
    """
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {VIDEO_W}
PlayResY: {VIDEO_H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Film,{_font_name(project)},{SUB_FONTSIZE},&H00FFFFFF,&H000000FF,&HB4000000,&H00000000,0,0,0,0,100,100,0,0,1,2.4,1.2,2,120,120,{SUB_MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
"""

    def ass_time(t: float) -> str:
        h, rem = divmod(max(t, 0), 3600)
        m, s = divmod(rem, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"

    events = []
    for start, end, body in _parse_srt(srt.read_text(encoding="utf-8")):
        text = body.replace("\n", "\\N")
        # Exactly 9 fields: Layer,Start,End,Style,Name,MarginL,MarginR,Effect,Text
        # One extra comma pushes "0" into Effect and every line renders with a
        # leading comma.
        events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Film,,0,0,,{text}")

    ass = srt.with_suffix(".ass")
    ass.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return ass


def subtitle_filter(srt: Path, project: str) -> str:
    """Burn in subtitles: bottom-centred, white with a thin outline, no box.

    A background box is broadcast styling, not cinema.
    """
    ass = srt_to_ass(srt, project)
    return f"ass={ass}"


ROOT = Path(__file__).resolve().parent
CLIPS = ROOT / "out"
MUSIC_API = "pika/pika-audio/pika-music"

# Prompt direction matters more than the model. An earlier brief asked for
# "restrained, sparse solo piano, never bombastic" and came back cold and
# agitated — which is not the same request as "gentle".
# Fallback score brief. Projects override with their own MUSIC_PROMPT.
#
# Instrument family matters more than mood: a Western orchestra under a film
# that is not Western is simply wrong. And note that "restrained, sparse, never
# bombastic" reads back as *cold and agitated* — it is not the same request as
# "gentle".
MUSIC_PROMPT = (
    "Restrained instrumental score for a character drama. Sparse solo piano over a low "
    "sustained string bed, entering almost imperceptibly. A slow swell in the middle third "
    "using low brass and cello, never bombastic. Resolves to solo piano and near-silence at "
    "the end. Wide dynamic range, long reverb tail, no percussion, no drums, no choir, "
    "no synth arpeggios. Melancholy, spacious, patient."
)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def resolve_clip(shot_id: str, project: str) -> Path | None:
    """Clips live in out_<project>/<shot_id>.mp4."""
    clip = ROOT / f"out_{project}" / f"{shot_id}.mp4"
    return clip if clip.is_file() else None


def concat(project: str) -> Path:
    """Concatenate with the concat FILTER, applying per-clip fades in the same graph.

    Not the concat demuxer: source clips are HEVC, and any clip re-encoded to add
    a fade becomes h264. The demuxer requires identical codecs across inputs;
    mixing them raises "Error splitting the input into NAL units", silently drops
    about a quarter of the runtime, and still EXITS 0. Observed: a 120s film came
    out 91.5s with no error.

    The concat filter joins after decoding, so mixed codecs are fine.
    """
    clips, shots = [], []
    for shot in shot_list(project):
        clip = resolve_clip(shot['id'], project)
        if clip:
            clips.append(clip)
            shots.append(shot)
        else:
            print(f"warning: missing {shot['id']}, skipping", file=sys.stderr)

    inputs: list[str] = []
    graph: list[str] = []
    labels: list[str] = []
    for i, (clip, shot) in enumerate(zip(clips, shots)):
        inputs += ["-i", str(clip)]
        fade_in, fade_out = fades(project).get(shot["id"], (0.0, 0.0))
        v = [f"[{i}:v]setpts=PTS-STARTPTS", "format=yuv420p"]
        a = [f"[{i}:a]asetpts=PTS-STARTPTS", "aresample=48000"]
        if fade_in:
            v.append(f"fade=t=in:st=0:d={fade_in}:color=black")
            a.append(f"afade=t=in:st=0:d={fade_in}")
        if fade_out:
            st = shot["duration"] - fade_out
            v.append(f"fade=t=out:st={st}:d={fade_out}:color=black")
            a.append(f"afade=t=out:st={st}:d={fade_out}")
        graph.append(",".join(v) + f"[v{i}]")
        graph.append(",".join(a) + f"[a{i}]")
        labels += [f"[v{i}]", f"[a{i}]"]

    graph.append("".join(labels) + f"concat=n={len(clips)}:v=1:a=1[v][a]")

    raw = ROOT / f"{project}-raw.mp4"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        *inputs,
        "-filter_complex", ";".join(graph),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(raw),
    ])
    return raw


def make_music(seconds: int, prompt: str = "", out: Path | None = None) -> Path | None:
    client = PikaClient(load_config())
    payload = {"prompt": prompt or MUSIC_PROMPT, "duration": float(seconds), "mode": "text_to_music"}
    print(f"generating {seconds}s of score…", flush=True)
    try:
        job = client.submit(MUSIC_API, payload)
        finished = client.wait(job.request_id, poll_interval_s=8.0, max_wait_s=900.0)
        result = finished.raw.get("output") or client.content(job.request_id)
    except Exception as exc:
        print(f"score generation failed, skipping: {exc}", file=sys.stderr)
        return None
    url = find_asset_url(result)
    if not url:
        print("score returned no asset URL, skipping", file=sys.stderr)
        return None
    return download(url, out or ROOT / "score.mp3")


def _envelope(clip: Path) -> tuple[list[float], float]:
    """Loudness envelope in dBFS at 0.2s granularity, plus the step size."""
    import audioop
    import wave

    tmp = ROOT / ".probe.wav"
    run([
        "ffmpeg", "-v", "error", "-y", "-i", str(clip),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(tmp),
    ])
    with wave.open(str(tmp)) as w:
        fr, data = w.getframerate(), w.readframes(w.getnframes())
    tmp.unlink(missing_ok=True)
    step = int(fr * 0.2) * 2
    levels = [
        20 * math.log10(max(audioop.rms(data[i:i + step], 2), 1) / 32768)
        for i in range(0, max(len(data) - step, 1), step)
    ]
    return levels, 0.2


def _speech_anchors(clip: Path, count: int, dur: float) -> list[float]:
    """The `count` strongest speech moments, in seconds from the clip start.

    Threshold segmentation is unreliable on this material: some shots have only
    ~10 dB between the ambience floor and the dialogue peak, with speech buried
    in crowd tone. Any fixed threshold either detects nothing or shatters into
    fragments.

    Peak anchoring instead: ask for N moments, get exactly N, each landing where
    there is real energy. This is a FALLBACK — it is still guessing. Word-level
    timestamps from a transcription model are the real answer.
    """
    levels, res = _envelope(clip)
    if not levels or count <= 0:
        return []

    # 3-point moving average to flatten single-frame spikes
    smooth = [
        sum(levels[max(0, i - 1):i + 2]) / len(levels[max(0, i - 1):i + 2])
        for i in range(len(levels))
    ]
    guard = int(1.5 / res)          # peaks must be at least 1.5s apart
    work = smooth[:]
    picks: list[int] = []
    for _ in range(count):
        i = max(range(len(work)), key=lambda k: work[k])
        if work[i] == -999:
            break
        picks.append(i)
        for k in range(max(0, i - guard), min(len(work), i + guard + 1)):
            work[k] = -999
    picks.sort()
    return [min(p * res, max(dur - 1.0, 0.0)) for p in picks]


def _speech_regions(clip: Path, sens: float = 5.0) -> list[tuple[float, float]]:
    """Detect speech regions in one clip, in seconds from its start."""
    import audioop
    import wave

    tmp = ROOT / ".probe.wav"
    run([
        "ffmpeg", "-v", "error", "-y", "-i", str(clip),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(tmp),
    ])
    with wave.open(str(tmp)) as w:
        fr, data = w.getframerate(), w.readframes(w.getnframes())
    tmp.unlink(missing_ok=True)

    step = int(fr * 0.2) * 2
    levels = [
        20 * math.log10(max(audioop.rms(data[i:i + step], 2), 1) / 32768)
        for i in range(0, max(len(data) - step, 1), step)
    ]
    if not levels:
        return []
    floor = sorted(levels)[int(len(levels) * 0.3)]
    thr = floor + sens

    regions, cur = [], None
    for i, v in enumerate(levels):
        t = i * 0.2
        if v > thr:
            cur = [t, t] if cur is None else [cur[0], t]
        elif cur:
            if cur[1] - cur[0] >= 0.3:
                regions.append((cur[0], cur[1] + 0.2))
            cur = None
    if cur and cur[1] - cur[0] >= 0.3:
        regions.append((cur[0], cur[1] + 0.2))

    # Merge regions less than 0.35s apart — that is a pause inside one line
    merged: list[list[float]] = []
    for s, e in regions:
        if merged and s - merged[-1][1] < 0.35:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


_PUNCT = set("，。、—…！？；：,.!?;:\"'「」“”‘’ ()（）")

_LINE_RE = re.compile(r"「([^」]+)」|\"([^\"]+)\"|“([^”]+)”")


def extract_lines(dialogue: str) -> list[str]:
    """Pull the spoken lines out of a dialogue block, accepting every quote style.

    English scripts use "...", Chinese uses 「」. A regex that knows only one
    silently yields zero lines for the other language — which also disables the
    fallback placement, so you get an empty subtitle file and no error.
    """
    return [a or b or c for a, b, c in _LINE_RE.findall(dialogue)]


def _norm_token(text: str) -> str:
    return "".join(ch for ch in text.strip().lower() if ch not in _PUNCT)


def _line_tokens(line: str) -> list[str]:
    """Tokenise by language: words for Latin scripts, characters for Chinese.

    The transcription model returns per-character tokens for Chinese and
    per-word tokens for English. Both sides must use the same granularity —
    comparing letters to words matches nothing, forever, with no error.
    """
    if re.search(r"[A-Za-z]", line):
        return [t for t in re.findall(r"[a-z0-9']+", line.lower()) if t]
    return [c for c in line if c not in _PUNCT]


def shot_list(project: str) -> list[dict]:
    return project_module(project).SHOTS


def _total(project: str) -> int:
    """Intended runtime in seconds. Always compute it from THIS project.

    An earlier version read a module-level constant belonging to a different
    film. Any project of a different length then had its score fade out at the
    wrong moment — silently, with no error and exit code 0.
    """
    return sum(x["duration"] for x in shot_list(project))


def _srt_name(project: str) -> str:
    return f"dialogue-{project}.srt"


def _tidy(cues: list[tuple[float, float, str]]) -> list[tuple[float, float, str]]:
    """Tidy pass: nudge earlier, enforce a minimum duration, cap by length, de-overlap.

    **Do not sort.** The input order is script order, and script order is the
    correct playback order. Sorting by timestamp reorders dialogue: a short line
    ("Traffic.") is textually contained in a neighbouring long one, the matcher
    picks the wrong occurrence, and sorting then swaps the two lines.

    Keep script order and only push backwards-running timestamps forward.
    """
    out: list[list] = []
    for start, end, body in cues:
        s = max(0.0, start - 0.2)
        if out and s < out[-1][1]:      # never start before the previous cue ends
            s = out[-1][1] + 0.05
        cap = max(1.4, len(body) * 0.26 + 0.8)
        e = min(max(end + 0.35, s + 1.3), s + cap)
        if e <= s:
            e = s + 0.9
        out.append([s, e, body])
    for i in range(len(out) - 1):
        limit = out[i + 1][0] - 0.08
        if out[i][1] > limit:
            out[i][1] = max(limit, out[i][0] + 0.5)
    return [(s, e, b) for s, e, b in out]


def _write_srt(path: Path, cues: list[tuple[float, float, str]]) -> None:
    path.write_text(
        "\n\n".join(
            f"{i}\n{_fmt(s)} --> {_fmt(e)}\n{_wrap(b)}"
            for i, (s, e, b) in enumerate(cues, 1)
        ) + "\n",
        encoding="utf-8",
    )


def scribe_words(video: Path, project: str) -> list[dict] | None:
    """Normalise the audio, transcribe it, return word-level timestamps.

    The normalisation IS the trick. Generated dialogue commonly sits at -37 to
    -40 dBFS under ambience; fed raw, the transcription model returns timings
    10+ seconds out (one line measured at 30.15s was actually spoken at 37.30s).
    After highpass + compand + loudnorm, word timings land within ~0.2s.
    """
    from pika_api.uploads import upload_file

    wav = ROOT / ".scribe.wav"
    run([
        "ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
        "-af", "highpass=f=90,"
               "compand=attacks=0.02:decays=0.4:points=-70/-24|-40/-12|-20/-6|0/-3,"
               "loudnorm=I=-14:TP=-1.5",
        "-c:a", "pcm_s16le", str(wav),
    ])
    try:
        client = PikaClient(load_config())
        url = upload_file(client, wav)
        job = client.submit(
            "elevenlabs/eleven-scribe/transcription",
            {"audio_url": url, "duration_seconds": float(_total(project)), "diarize": True},
        )
        finished = client.wait(job.request_id, poll_interval_s=5.0, max_wait_s=900.0)
        result = finished.raw.get("output") or client.content(job.request_id)
    except Exception as exc:
        print(f"transcription failed, falling back to peak anchoring: {exc}", file=sys.stderr)
        return None
    finally:
        wav.unlink(missing_ok=True)

    node = (result or {}).get("transcript") if isinstance(result, dict) else None
    url = node.get("url") if isinstance(node, dict) else None
    if not url:
        return None
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "pika-quickstart/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    words = [w for w in data.get("words", []) if w.get("type") == "word"]
    print(f"{len(words)} word-level timestamps")
    return words or None


def align_to_words(
    lines: list[str], words: list[dict]
) -> tuple[list[tuple[float, float, str]], list[int]]:
    """Align script lines to word timings by walking both forward together.

    Script order and audio order are identical, so no fuzzy whole-sentence
    matching is needed: find which word the line starts on and which it ends on.

    Returns (aligned cues, indices of the lines that aligned). Lines that did not
    align are left for fallback placement — they must still be subtitled,
    because the plot information in them cannot be lost.
    """
    cues: list[tuple[float, float, str]] = []
    matched_idx: list[int] = []
    wi = 0
    for li, line in enumerate(lines):
        target = _line_tokens(line)
        if not target or wi >= len(words):
            continue

        # find the first token inside a forward-looking window
        start_i = next(
            (s for s in range(wi, min(wi + 90, len(words))) if _norm_token(words[s]["text"]) == target[0]),
            wi,
        )
        # consume greedily, remembering the last match
        ti, wj, last = 0, start_i, start_i
        while wj < len(words) and ti < len(target):
            if _norm_token(words[wj]["text"]) == target[ti]:
                last = wj
                ti += 1
            wj += 1
            if wj - start_i > max(len(target) * 3, 24):
                break

        matched = ti / len(target)
        if matched < 0.35:          # not heard; leave it for fallback placement
            continue
        start_t = float(words[start_i]["start"])
        end_t = float(words[last]["end"])
        # The timeline must stay monotonic: the script is ordered, so subtitles
        # cannot run backwards. Without this gate one line matches an earlier
        # word than its predecessor and everything after it desynchronises.
        if cues and start_t < cues[-1][1]:
            continue
        cues.append((start_t, end_t, line))
        matched_idx.append(li)
        wi = last + 1
    return cues, matched_idx


def build_srt_from_shots(project: str, raw_video: Path | None = None) -> Path:
    """Time every line per shot, using the script as ground truth.

    Which shot a line belongs to is known exactly, and shot boundaries are exact,
    so the only open question is where inside its own shot each line falls.

    Primary path: word-level timestamps from a transcription model. Fallback:
    energy-based anchoring within the shot. Never fuzzy-match a whole film's
    dialogue against a whole film's transcript — that is how subtitles end up
    ten seconds ahead of the speech.
    """
    # Primary path: word-level timestamps — the only real way to time from audio.
    if raw_video is not None:
        words = scribe_words(raw_video, project)
        if words:
            # Flatten the lines, remembering which shot each belongs to
            flat: list[str] = []
            owner: list[tuple[float, float]] = []   # (shot start, shot end)
            clock0 = 0.0
            for shot in shot_list(project):
                for ln in extract_lines(shot["dialogue"]):
                    flat.append(ln)
                    owner.append((clock0, clock0 + shot["duration"]))
                clock0 += shot["duration"]

            aligned, matched = align_to_words(flat, words)
            if len(aligned) >= max(3, len(flat) * 0.5):
                # Lines the model never spoke still need cues: the plot
                # information matters and reads as a radio caption. Place them
                # inside their own shot, between the neighbouring aligned cues.
                by_idx = dict(zip(matched, aligned))
                filled: list[tuple[float, float, str]] = []
                for i, line in enumerate(flat):
                    if i in by_idx:
                        filled.append(by_idx[i])
                        continue
                    lo, hi = owner[i]
                    prev_end = filled[-1][1] if filled else lo
                    nxt = next((by_idx[j][0] for j in range(i + 1, len(flat)) if j in by_idx), hi)
                    a = max(lo, prev_end + 0.3)
                    b = min(hi, nxt - 0.3)
                    if b - a < 1.0:                     # no gap; sit mid-shot instead
                        a = max(lo, min(hi - 1.6, (lo + hi) / 2 - 0.8))
                        b = a + 1.6
                    filled.append((a, min(b, a + max(1.6, len(line) * 0.26 + 0.8)), line))

                srt = ROOT / _srt_name(project)
                _write_srt(srt, _tidy(filled))
                print(
                    f"subtitles -> {srt.name} ({len(filled)} cues: {len(aligned)} aligned, "
                    f"{len(filled) - len(aligned)} placed by fallback)"
                )
                return srt
            print(
                f"only {len(aligned)}/{len(flat)} lines aligned; falling back to anchoring",
                file=sys.stderr,
            )

    cues: list[tuple[float, float, str]] = []
    clock = 0.0
    for shot in shot_list(project):
        dur = float(shot["duration"])
        lines = extract_lines(shot["dialogue"])
        if not lines:
            clock += dur
            continue

        clip = resolve_clip(shot["id"], project)
        anchors = _speech_anchors(clip, len(lines), dur) if clip else []
        if len(anchors) < len(lines):
            # Fallback: lay the lines out across 25%-90% of the shot, weighted
            # by length. Do not start at 0: generated shots almost always
            # establish the frame for a beat before anyone speaks.
            a, b = dur * 0.25, dur * 0.90
            total = sum(len(x) for x in lines) or 1
            anchors, t = [], a
            for line in lines:
                anchors.append(t)
                t += (b - a) * len(line) / total

        for i, (line, at) in enumerate(zip(lines, anchors)):
            start = max(0.0, at - 0.25)         # convention: cue slightly early
            # Duration from length: ~0.26s per Chinese character, plus 0.7s slack
            want = max(1.4, len(line) * 0.26 + 0.7)
            limit = (anchors[i + 1] - 0.35) if i + 1 < len(anchors) else dur
            end = min(start + want, limit, dur)
            if end - start < 0.9:               # too short to read; overrun slightly
                end = min(start + 0.9, dur)
            cues.append((clock + start, clock + end, line))
        clock += dur

    # Strict de-overlap: the later cue keeps its start, the earlier one is trimmed
    for i in range(len(cues) - 1):
        limit = cues[i + 1][0] - 0.08
        if cues[i][1] > limit:
            cues[i] = (cues[i][0], max(limit, cues[i][0] + 0.5), cues[i][2])

    srt = ROOT / _srt_name(project)
    _write_srt(srt, cues)
    print(f"subtitles -> {srt.name} ({len(cues)} cues, timed per shot)")
    return srt


def make_srt(video: Path, project: str) -> Path | None:
    """Extract audio, upload, transcribe to SRT. A real timeline, not an estimate."""
    from pika_api.uploads import upload_file

    wav = ROOT / ".dialogue.wav"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav),
    ])
    client = PikaClient(load_config())
    print("transcribing…", flush=True)
    try:
        url = upload_file(client, wav)
        job = client.submit(
            "openai/whisper/transcription",
            {
                "audio_url": url,
                "duration_seconds": float(_total(project)),
                "language": "zh",
                "response_format": "srt",
            },
        )
        finished = client.wait(job.request_id, poll_interval_s=5.0, max_wait_s=600.0)
        result = finished.raw.get("output") or client.content(job.request_id)
    except Exception as exc:
        print(f"transcription failed, skipping subtitles: {exc}", file=sys.stderr)
        return None
    finally:
        wav.unlink(missing_ok=True)

    # The transcript comes back as a URL to a .txt, not inline — go fetch it.
    text = result if isinstance(result, str) else ""
    if isinstance(result, dict):
        for key in ("srt", "text", "transcript", "content", "output"):
            node = result.get(key)
            if isinstance(node, str) and not node.startswith("http"):
                text = node
                break
            url = None
            if isinstance(node, str) and node.startswith("http"):
                url = node
            elif isinstance(node, dict) and isinstance(node.get("url"), str):
                url = node["url"]
            if url:
                import urllib.request

                req = urllib.request.Request(url, headers={"User-Agent": "pika-quickstart/1.0"})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    text = resp.read().decode("utf-8", errors="replace")
                break

    if "-->" not in text:
        print(f"transcript is not SRT, skipping subtitles: {text[:300]}", file=sys.stderr)
        return None

    srt = ROOT / _srt_name(project)
    srt.write_text(polish_srt(text, project), encoding="utf-8")
    print(f"subtitles -> {srt.name}")
    return srt


def _script_lines(project: str) -> list[str]:
    """Every 「…」 / "…" line from the shot script, in script order.

    Script order is authoritative: it is the same order the audio is in, so the
    aligner walks both forward together. Never sort cues by timestamp.
    """
    lines: list[str] = []
    for shot in shot_list(project):
        lines += extract_lines(shot["dialogue"])
    return lines


def _parse_srt(text: str) -> list[tuple[float, float, str]]:
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        rows = [r for r in block.splitlines() if r.strip()]
        if len(rows) < 2:
            continue
        m = re.search(
            r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", block
        )
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        # Body = every row after the timing row, joined with newlines (which
        # become \N in ASS). Joining with a space collapses two-line subtitles
        # into one overlong line; falling back to rows[-1] deletes the first line.
        ti = next((k for k, r in enumerate(rows) if "-->" in r), 0)
        body = "\n".join(rows[ti + 1:]).strip()
        out.append((start, end, body.strip()))
    return out


def _fmt(t: float) -> str:
    h, rem = divmod(max(t, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def polish_srt(text: str, project: str) -> str:
    """Merge transcript fragments into whole lines and correct them against the script.

    Transcription splits one spoken line into 1-2 second fragments; cinema
    subtitles want the whole line. Recognition also mangles names and invented
    terms, and the script is the ground truth for spelling.
    """
    segs = _parse_srt(text)
    script = _script_lines(project)
    if not segs or not script:
        return text

    # Sequence alignment: both the script and the fragments are in order, so
    # consume a run of fragments per line. One line yields exactly one cue, which
    # avoids the duplicate-line artefact of merging before matching.
    cues: list[tuple[float, float, str]] = []
    si = 0
    for line in script:
        if si >= len(segs):
            break
        target = set(line)
        acc, best_j, best_score = "", si, 0.0
        for j in range(si, min(si + 6, len(segs))):
            acc += segs[j][2]
            score = len(set(acc) & target) / max(len(target), 1)
            if score > best_score:
                best_score, best_j = score, j
            if best_score > 0.9:
                break
        if best_score >= 0.45:
            cues.append((segs[si][0], segs[best_j][1], line))
            si = best_j + 1

    if not cues:
        return text
    return "\n\n".join(
        f"{i}\n{_fmt(s)} --> {_fmt(e)}\n{_wrap(b)}" for i, (s, e, b) in enumerate(cues, 1)
    ) + "\n"


def _wrap(line: str, limit: int = 18) -> str:
    """Wrap a long line onto two rows.

    Break Chinese at punctuation near the midpoint; break Latin scripts at the
    nearest space. Splitting English at the character midpoint yields "goin" /
    "g to".
    """
    is_latin = bool(re.search(r"[A-Za-z]", line))
    cap = 42 if is_latin else limit          # Latin fits more characters per row
    if len(line) <= cap:
        return line

    mid = len(line) // 2
    if is_latin:
        # Break only at spaces, preferring the midpoint; leave unwrapped if none
        spaces = [i for i, ch in enumerate(line) if ch == " "]
        if not spaces:
            return line
        cut = min(spaces, key=lambda i: abs(i - mid))
    else:
        best, best_d = None, 99
        for i, ch in enumerate(line):
            if ch in "，。、—…！？；":
                d = abs(i + 1 - mid)
                if d < best_d:
                    best, best_d = i + 1, d
        cut = best if best and 4 <= best <= len(line) - 3 else mid
    return line[:cut].rstrip() + "\n" + line[cut:].lstrip()


def mix(video: Path, music: Path, out: Path, project: str, srt: Path | None = None) -> Path:
    """Cards, burned-in subtitles, and a score ducked under the dialogue."""
    # Transitions were already applied per clip before concatenation.
    stages: list[str] = []
    cards = name_card_filter(project)
    if cards:
        stages.append(cards)
    if srt is not None:
        stages.append(subtitle_filter(srt, project))
    has_video_fx = bool(stages)
    video_chain = f"[0:v]{','.join(stages)}[vout];" if has_video_fx else ""
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(video), "-i", str(music),
        "-filter_complex",
        video_chain +
        # Denoise the dialogue stem first. "The background is very noisy" is not
        # a volume problem: generated ambience shares one track with the voices,
        # so lowering it lowers the dialogue too. Fix it in the frequency domain.
        #   highpass   cut sub-85Hz rumble (HVAC, traffic, room resonance)
        #   afftdn     FFT denoise; tn=1 tracks the noise floor rather than
        #              assuming a fixed one
        #   equalizer  put ~2dB back around 3kHz — denoising dulls the voice, and
        #              without this lift it reads as muffled
        # Then split: one path is audible, one is the sidechain key for ducking.
        "[0:a]highpass=f=85,afftdn=nf=-26:tn=1,"
        "equalizer=f=3000:t=q:w=1.2:g=2,asplit=2[dry][key];"
        f"[1:a]volume=-18dB,afade=t=in:st=0:d=4,afade=t=out:st={_total(project) - 6}:d=6[bed];"
        "[bed][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=600[ducked];"
        "[dry][ducked]amix=inputs=2:duration=first:dropout_transition=0,"
        "loudnorm=I=-16:TP=-1.5:LRA=11[aout]",
        "-map", "[vout]" if has_video_fx else "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "192k",
        str(out),
    ])
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble, subtitle, score and mix a generated film."
    )
    parser.add_argument("--project", required=True,
                        help="project name; loads shots_<name>.py, reads out_<name>/")
    parser.add_argument("--no-music", action="store_true", help="skip the score")
    parser.add_argument("--no-subs", action="store_true", help="skip transcription/subtitles")
    parser.add_argument("--srt", default="", help="reuse an existing SRT, skip transcription")
    parser.add_argument("--score", default="", help="reuse an existing score, skip generation")
    args = parser.parse_args(argv)
    project = args.project

    raw = concat(project)
    print(f"concatenated -> {raw.name}")

    if args.no_music:
        # A no-music cut needs MORE denoising, not less: with no score to mask it,
        # the generated ambience floor is exposed. Returning right after concat
        # here — which an earlier version did — is exactly backwards.
        out = ROOT / f"{project}-nomusic.mp4"
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
            "-af", "highpass=f=85,afftdn=nf=-26:tn=1,"
                   "equalizer=f=3000:t=q:w=1.2:g=2,"
                   "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(out),
        ])
        print(f"no-music cut -> {out}")
        return 0

    srt: Path | None = None
    if not args.no_subs:
        srt = Path(args.srt) if args.srt else build_srt_from_shots(project, raw)

    # Score files are namespaced per project so two films never share one stem.
    default_score = ROOT / f"score-{project}.mp3"
    existing = Path(args.score) if args.score else default_score
    prompt = _attr(project, "MUSIC_PROMPT", MUSIC_PROMPT)
    music = existing if existing.is_file() else make_music(_total(project), prompt, default_score)
    if music is None:
        print("no score generated; raw cut is the deliverable", file=sys.stderr)
        return 1
    print(f"score -> {music.name}")

    final = mix(raw, music, ROOT / f"{project}-final.mp4", project, srt)
    print(f"final -> {final}")
    run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
         "-show_entries", "stream=codec_type,width,height",
         "-of", "default=noprint_wrappers=1", str(final)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
