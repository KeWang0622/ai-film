# Post-production

All of this is free and re-runnable. Never regenerate a shot to fix something that
lives here.

## Concatenation

Use the concat **filter**, not the demuxer.

```python
# per input i: normalise timestamps, grade, then fade the PICTURE only
dur = probe_duration(clip)                      # real, not declared: clips run ~0.06s long
v = [f"[{i}:v]setpts=PTS-STARTPTS", "format=yuv420p"]
if MONOCHROME: v += [MONO_FILTER, "format=yuv420p"]
if GRAIN:      v += [f"noise=alls={GRAIN}:allf=t+u", "format=yuv420p"]
if fade_in:    v.append(f"fade=t=in:st=0:d={fade_in}:color=black")
if fade_out:   v.append(f"fade=t=out:st={dur - fade_out:.3f}:d={fade_out}:color=black")
a = [f"[{i}:a]asetpts=PTS-STARTPTS", "aresample=48000"]
# audio fades ONLY at the head of the film and the tail of the film
...
graph.append("".join(labels) + f"concat=n={n}:v=1:a=1[v][a]")
```

**Why not the demuxer:** it requires identical codecs across inputs. Source clips
are HEVC; any clip you re-encode (e.g. to add a fade) becomes h264. Mixing them
produces `Error splitting the input into NAL units`, silently drops ~25% of the
runtime, and **exits 0**. Observed: a 120s film became 91.5s with no error.

## Transitions

`fade` only works at the head and tail of a stream. `fade=t=in:st=108` does not
mean "fade in at 108s" — it renders every frame *before* 108s black. Two such
filters on a master will black out almost the entire film (observed: an 86 MB
output became 3.2 MB).

Do dips inside the adjacent clips, as above. Runtime is unchanged, so an exact
120s stays exactly 120s.

Assign by narrative function, keyed by shot id:

```python
FADES = {
    "04-boarding": (0.0, 0.5),   # leaving Earth
    "05-gate":     (0.5, 0.0),
    "09-alone":    (0.0, 0.8),   # time starts passing
    "10-beacon":   (0.8, 0.9),
    "11-spring":   (0.9, 0.0),   # decades later
}
```

Everything not listed is a hard cut, including disaster and immediate aftermath —
a transition there telegraphs the event and kills the impact.

### Dips are picture-only

The earlier recipe faded audio with the picture. Measured on a real film, the first
line of the shot after a dip began at **0.00 s**; a 0.35 s audio fade-in sits right
on top of it. In a controlled test that fade took **17 dB** off the first syllable,
while the picture dip looked identical with or without it.

```
fade the image at every dip; never fade the audio at a clip boundary
fade the audio only at the very head and the very tail of the film
```

Sound carrying through a cut to black is ordinary film grammar, and nobody hears
the join. Check it anyway: `verify_film.py` prints speech energy in the first
0.35 s after every dip and marks any shot where a line starts there.

### Where the dips go

Hard cut inside a scene. **Dip at every jump in time or place** — into a flashback
and out of it, night to dawn, one country to another. A recut that left three such
jumps on hard cuts read to its first viewer as though the film had skipped.

## Subtitles

### Timing

```
raw video
  → extract mono 16k
  → highpass=f=90,
    compand=attacks=0.02:decays=0.4:points=-70/-24|-40/-12|-20/-6|0/-3,
    loudnorm=I=-14:TP=-1.5
  → upload → elevenlabs/eleven-scribe/transcription (diarize: true)
  → transcript JSON at .transcript.url  (fetch it; it is not inline)
  → align script lines to word timings
```

**The normalisation is the whole trick.** Generated dialogue commonly sits at
−37 to −40 dBFS under ambience. Fed raw, transcription returns timings that are
10+ seconds off — one line measured at 30.15s was actually spoken at 37.30s.
After compansion, word-level timings land within ~0.2s.

Energy-based placement (RMS peak picking) is *not* a substitute. Some shots have
only 10 dB of dynamic range between ambience and dialogue; peak picking is still
guessing. It got the same line wrong by 7 seconds.

### Alignment

Script order and audio order are identical, so walk both forward:

```python
for li, line in enumerate(lines):
    target = _line_tokens(line)                      # language-aware!
    start_i = next((s for s in range(wi, min(wi+90, len(words)))
                    if _norm_token(words[s]["text"]) == target[0]), wi)
    ti, wj, last = 0, start_i, start_i
    while wj < len(words) and ti < len(target):
        if _norm_token(words[wj]["text"]) == target[ti]:
            last = wj; ti += 1
        wj += 1
        if wj - start_i > max(len(target)*3, 24):
            break
    if ti/len(target) >= 0.35:
        cues.append((words[start_i]["start"], words[last]["end"], line))
        wi = last + 1
```

**Tokenise by language.** Scribe returns per-character tokens for Chinese and
per-word tokens for English. Comparing letters to words matches nothing and
produces a 1-byte subtitle file with no error.

```python
def _line_tokens(line):
    if re.search(r"[A-Za-z]", line):
        return re.findall(r"[a-z0-9']+", line.lower())
    return [c for c in line if c not in _PUNCT]
```

Extract dialogue with a regex that accepts every quote style you use
(`「」`, `"…"`, `“…”`) — one that only knows Chinese brackets silently yields zero
English lines and disables the fallback too.

### Lines the model never spoke

Some dialogue simply isn't in the audio. Do not drop those cues — the plot
information matters and reads as a radio caption. Place them inside their own
shot's window, between the neighbouring aligned cues.

### Rendering

Emit ASS with explicit resolution; do not use `subtitles=...:force_style`.

```
[Script Info]
PlayResX: 2206
PlayResY: 946
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, ..., MarginL, MarginR, MarginV, Encoding
Style: Film,DejaVu Sans,50,&H00FFFFFF,&H000000FF,&HB4000000,&H00000000,0,0,0,0,
       100,100,0,0,1,2.4,1.2,2,120,120,46,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, Effect, Text
Dialogue: 0,0:00:01.36,0:00:04.39,Film,,0,0,,line one\Nline two
```

- `force_style` assumes `PlayResY: 288`; on a 946-tall video libass multiplies
  FontSize and MarginV by ~3.3 — text renders huge and floats well above the
  bottom edge.
- `Dialogue:` takes **exactly 9 fields**. An extra comma pushes `0` into Effect
  and every line renders with a leading comma.
- Font: CJK needs `Droid Sans Fallback` or WenQuanYi; Latin looks better in
  `DejaVu Sans`.
- Cinema defaults: FontSize ≈ 5% of height, MarginV ≈ 5%, white with a 2–2.5px
  semi-transparent outline, no background box (that is broadcast, not cinema).

### Wrapping

```python
is_latin = bool(re.search(r"[A-Za-z]", line))
cap = 42 if is_latin else 18
```

Break Chinese at punctuation near the midpoint; break English at the nearest
space. Splitting English at the character midpoint yields `goin` / `g to`.

When converting SRT→ASS, take *every* row after the timing row and join with
`\n` → `\N`. Joining with a space collapses two-line subtitles into one overlong
line; falling back to `rows[-1]` deletes the first line entirely.

## Score and mix

**First decide whether to score at all.** On two dialogue-driven remakes the viewer
asked for the score to be removed — even ducked, with speech holding 69–79% of the
spectrum under it, it read as competing with the lines. Default to no score
(`SCORE = False`) and offer one.

If you do score, generate it separately and duck it under the dialogue:

```
[0:a]asplit=2[dry][key];
[1:a]volume=-18dB,afade=t=in:st=0:d=4,afade=t=out:st={TOTAL-6}:d=6[bed];
[bed][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=600[ducked];
[dry][ducked]amix=inputs=2:duration=first:dropout_transition=0,
loudnorm=I=-16:TP=-1.5:LRA=11[aout]
```

The dialogue track drives its own ducking as the sidechain key, so music steps
back automatically when anyone speaks.

Prompt direction matters more than the model. "Restrained, sparse solo piano,
never bombastic" reads as cold and agitated in context. For epic warmth ask for a
sustained cello/viola bed with violins entering high and soft, French horns
underneath, one long unhurried crescendo, legato throughout — and explicitly
exclude percussion, timpani, brass stabs, choir, synth arpeggios and dissonance.

## Verify every render

```bash
ffprobe -v error -show_entries format=duration,size,bit_rate \
        -show_entries stream=codec_type,codec_name,width,height \
        -of default=noprint_wrappers=1 out.mp4
ffmpeg -v error -y -ss 64 -i out.mp4 -frames:v 1 frame.png   # then look at it
```

Check duration against the intended total and file size against expectation. In
this pipeline the normal failure mode is silent truncation with exit code 0 —
not an exception, not a warning.

---

# Additions from the next ten films

## Denoising dialogue

"The background is very noisy" is not a volume problem — the generated ambience
(hospital hum, office floor, terminal reverb) shares one track with the voices, so
lowering it lowers the dialogue too. Fix it in the frequency domain:

```
highpass=f=85            # HVAC, traffic, room rumble
afftdn=nf=-26:tn=1       # FFT denoise, tn=1 tracks the noise floor
equalizer=f=3000:t=q:w=1.2:g=2   # put speech clarity back
```

The last stage matters. Denoising dulls the voice; without the ~3 kHz lift it reads
as muffled and the user will say so. Run the chain before the sidechain split so
both the audible path and the ducking key are cleaned.

A no-music cut needs *more* denoising, not less — there is no score to mask the
floor.

## A no-music path still needs the audio chain

`--no-music` returning right after concat skips normalisation and denoising
entirely, which is exactly backwards. Give it its own branch:

```python
# two-pass LINEAR loudnorm - deliver.loudnorm_linear()
pre = "highpass=f=85,afftdn=nf=-26:tn=1,equalizer=f=3000:t=q:w=1.2:g=2"
loudnorm_linear(raw, out, pre=pre)     # pass 1 measures WITH pre; pass 2 applies one gain
```

**Single-pass `loudnorm` is the wrong tool for a finished film.** It is a dynamic
compressor, and a film's quiet passages are deliberate. Controlled test on the same
cut:

| | title (silent) | dialogue | gap |
|---|---|---|---|
| raw cut | −65.5 dBFS | −29.0 | 36.4 dB |
| single-pass `loudnorm` | **−15.8** | −11.9 | **3.9 dB** |
| two-pass `linear=true` | −51.4 | −11.5 | 39.9 dB |

On a real black-and-white film the silent title card came out at −17 dBFS — audible
hiss — single-pass, and −42 dBFS linear.

## Score generation

`pika/pika-audio/pika-music` is deprecated for this work. Options that do work:

- **`minimax/minimax-music-3.0/text-to-audio`** with `is_instrumental: true`.
  Output is ~105 s with **no duration parameter**. For a 160–200 s film, generate
  two pieces with different briefs — an "early years" and a "later, resolved"
  version — and crossfade them. That maps onto the film's turn and sounds better
  than looping one cue.
- **`pika/pika-audio/pika-soundtrack`** takes the *video* and scores to picture.
  It replaces the entire audio track, so instruct it to produce instrumental music
  only with no voices or effects, then mix that stem under the original dialogue.
- **`bytedance/seed-audio-1.0/text-to-audio`** is a TTS/dialogue model. Instrumental
  prompts are rejected by its speech safety audit (`audio risk audit
  tts_create_output: chunk 0 rejected`). Not usable for score.

Prompt length matters: a ~150-word music brief failed on seed-audio with
`provider_error` in 5 s where a one-line brief succeeded.

## Score direction by genre

Getting the instrument family wrong is worse than getting the mood wrong. A Western
orchestra under a Tang-dynasty pilgrimage or a Han-dynasty war film is simply wrong.

| Film | Palette |
|---|---|
| Chinese mythological journey | guqin, xun ocarina drone, bamboo dizi, erhu; sparse, long decay, stone-canyon reverb |
| Chinese war epic | guqin and low erhu, xiao flute, a war drum struck *singly and widely spaced* — never a march |
| Immigrant family drama | solo upright piano with audible felt hammers and room sound, one cello in the middle third, ends on a held note with the pedal down |

Always exclude explicitly: percussion stabs, timpani, choir, synth arpeggios,
trailer builds, fanfare. And note that "restrained, sparse, never bombastic" reads
as *cold and agitated* — it is not the same request as "gentle".

## Act boundaries

Beyond the time-ellipsis rule, use a dip to black to separate **acts or self-
contained episodes**, and hard-cut everything inside them.

```python
FADES = {
  "00-title":      (0.8, 0.8),   # card, isolated at both ends
  "01-first":      (0.8, 0.0),
  "04-act-one-end":(0.0, 0.8),
  "05-act-two":    (0.8, 0.0),
  "11-final":      (0.7, 1.5),   # last shot fades out
  "12-end-card":   (1.2, 1.5),
}
```

**Namespace the keys.** This dict is shared across projects and two films will both
have `00-title` or `09-the-door`; a duplicate key silently applies one film's
transitions to another.

## Black and white, and grain

**Force it in post, whatever the prompt returned.** Whole shots have come back in
colour under a "true black and white" prompt.

```
colorchannelmixer=.42:.48:.10:0:.42:.48:.10:0:.42:.48:.10:0     panchromatic mix
curves=all='0/0 0.22/0.16 0.5/0.52 0.78/0.86 1/1'                  silver-gelatin curve
```

`hue=s=0` is not a substitute: it reads as drained colour footage, not as film stock.

**Verify with the 95th percentile of chroma, never the mean.** A mostly neutral frame
with one lamp and one blue door has a small mean chroma and an obvious colour
problem. After the conversion a real 3:48 master measured p95 = 2.0 across 50
samples; a vivid colour test clip run through the old pipeline measured 120.

**Add grain in post, not in the prompt**, so its texture is identical from cut to cut
(`noise=alls=5:allf=t+u` reads as 1940s stock; 2 as modern digital). Grain also
breaks up the banding that fog and soft gradients produce in 8-bit video — measured
median flat runs of 10–16 px on two films. Encode every grainy master with
`-tune grain`, or x264 smooths it away.

**Check banding away from dips.** A dip to black is one flat value across the whole
frame; sampling frame 0 once reported a 1,663 px "band".

## Verify runtime and loudness every time

```bash
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 final.mp4
ffmpeg -i final.mp4 -af loudnorm=print_format=summary -f null /dev/null 2>&1 | grep Input
```

Expect the sum of the **real** clip durations ±0.15 s (clips render ~0.06 s longer
than declared, so the declared total is always a little short), and −15 to −17 LUFS
integrated with true peak below −1 dBTP. A runtime short by 20% is the
concat-demuxer bug, which exits 0.

`verify_film.py` runs runtime, colour, music-leak, banding, speech-at-dip and
faststart checks in one pass and treats any unreadable measurement as a failure.
