---
name: ai-film
description: Produce multi-shot narrative short films (60–200s) with AI video generation — story architecture, shot design, locking a real person's face across dozens of shots, dialogue, burned-in subtitles timed from audio, score, transitions, and multi-language/multi-ending variants. Use when asked to make a short film, movie, cinematic video, trailer, or any multi-scene narrative video with recurring characters. Also use when an existing AI video looks "not cinematic", when characters drift or get swapped between shots, when someone's face stops looking like them, when props change between scenes, when subtitles don't match the speech, or when a finished video won't play in a browser.
---

# AI Film Production

Build a narrative short from a premise. Two stages: **generation** (paid, slow) and
**post-production** (free, fast, endlessly re-runnable). Keeping them in separate
scripts is the most important structural decision here — subtitles, transitions,
fonts, score and mixing get re-run dozens of times without spending again.

```
shots_<project>.py   scenes: shot design, identity, props, audio rules, dialogue
check_script.py      lints the shot script against this catalogue    free
generate.py          → out_<project>/*.mp4        paid, ~20–35 min for 12 shots
audit_faces.py       → audit_<project>/*.png      face verification, free
finish.py            → concat → subtitles → score → mix → final.mp4     free
```

Copy `templates/` into a working directory, then `cp shots_template.py
shots_<project>.py` and edit that. Every other script is generic and routes by
`--project <name>`. Run `check_script.py` before spending anything.

---

## The one rule everything else follows from

**The model executes descriptions. It does not execute negations. And it fills
every space you leave it.**

Nine times out of ten a defect is fixed by *changing what you described*, not by
adding another "NO …". Measured, repeatedly:

| Defect | Adding a negative | Changing the description |
|---|---|---|
| Extras appearing on a small boat | failed twice — "NO other passengers, NO crowd, NO boatman" | fixed first try — "shoot the whole boat bow to stern so the people can be counted" |
| A santa hat from the reference photo | failed | fixed — supply a **clean reference photo** |
| Calligraphy laid out wrong | failed twice | fixed — describe the physical sheet, not the forbidden layout |
| Two characters swapped for the whole film | n/a | fixed — remove the body-type adjectives that were fighting the photos |

Negatives still earn their place for *iconography* ("no opera makeup", "no fur on
the face") — they suppress a strong prior. They are near-useless for composition,
staging and headcount.

---

## Order of work

1. **Story first.** Premise → 8–13 scenes, three or four acts, uneven durations.
   Pick the recurring object and the spoken promise before writing any shot design.
   → `references/story.md`
2. **Check the subject for identity risk** (see below). This decides how much of
   your budget goes to reruns.
3. **Reference photos.** Real photos, clean background, face large, 2+ per person.
   → `references/identity.md`
4. **Write `shots_*.py`.** Six design elements per shot; dialogue carries all plot.
   → `references/prompting.md`
5. **Generate ONE shot with each new face and look at it — cropped.** Before
   spending on twelve.
6. **Generate the rest**, then iterate freely in post.
7. **Verify by cropping faces and comparing them to the reference side by side.**
   Exit code 0 means nothing here, and neither does a wide frame.

---

## Choose the subject knowing what it costs

**Subject choice is the single largest driver of identity cost.** A character with
a famous "standard face" will overwrite the actor's face, and no amount of prompt
work fully removes it.

| Subject | Result |
|---|---|
| Idiom fables, original stories, generic-period drama | **12/12 first pass**, zero identity reruns |
| *Dream of the Red Chamber* — famous but no face paint | 13/13 first pass |
| *Mulan* — famous but no fixed face | 11/13, 2 unrelated failures |
| *Journey to the West* — Monkey King | **3 full rounds of reruns** |
| *Three Kingdoms* — Guan Yu's red face and beard | **8 of 12 shots reshot** |

If the brief demands a high-prior character, budget the reruns up front and say so.
Then strip the entire iconography — not just the name. → `references/identity.md`

---

## Non-negotiable rules

Each of these cost a generation cycle to learn.

1. **Write shot design, not scene description.** LENS, FOREGROUND, FRAME, BLOCKING,
   EYELINE, MOVE. Without them: subject-centred, symmetrical, facing camera — a
   stock photo. Camera-body jargon buys texture, not cinema.
2. **The photograph wins.** Never write a physical attribute that contradicts the
   reference photo. Body-type adjectives override the `@ImageN` tag and the model
   will silently **swap two characters for an entire film**.
3. **Never age a face.** No de-aging, no aging-up, no child/teen variants. The era
   is carried by wardrobe, props, hair and set. This was corrected three times in
   one project before it stuck.
4. **Lock identity with hardware that exists in the photo.** Glasses *shape* (square
   vs round) is the most reliable discriminator found. Build, height and face shape
   are not — they fool you in profile and in low light.
5. **A recurring prop needs a fixed description block, exactly like a character.**
   "A small notebook" yields a different notebook every scene and the object's
   three-beat silently breaks.
6. **Three simultaneous demands per shot, maximum.** Ask for five and the model
   does the cheapest one.
7. **Never let the video model score the film.** It composes music, the music trips
   copyright moderation, and the job fails *after* rendering — you pay, you get
   nothing. Ban it in every prompt; add score in post.
8. **Title and end cards must be declared `ABSOLUTELY SILENT`.** With no dialogue
   the model invents ambience or music and trips the same copyright filter.
9. **Max three speakers and five lines per shot.** Beyond that the model loses the
   turn-taking and has two characters say the same line in unison. Add an explicit
   one-speaker-per-line rule to the global audio block.
10. **Adding to a prompt weakens what is already in it.** A long new prop block let
    Christmas wardrobe back in through a constraint that had been holding. After
    lengthening a prompt, re-verify what previously passed.
11. **`provider_timeout` is not a content problem.** A ~20-minute server ceiling,
    driven by queue load, not shot complexity. Retry unchanged.
12. **Never use a negative for headcount or framing.** Define the frame so the wrong
    answer has nowhere to live.

---

## Verification is a procedure, not a glance

Three separate defects shipped past a "verified" wide frame — a soft out-of-focus
face, a face that had drifted to a stranger, and **two leads swapped for the entire
film**. All three were found by the user, not by the check.

```
For every shot with a face:
  1. Crop the face region and scale it up
  2. Put it beside the reference photograph
  3. Judge by glasses shape / hardware — not by face shape
  4. Confirm WHICH person is wearing WHICH costume
```

`templates/audit_faces.py` does the contact sheets. Also verify: the recurring prop
is the same object; the rhyming shots actually match; anyone who must not be shown
is not shown.

---

## Subtitles: time them from the audio

Generated dialogue often sits at −37 dBFS under ambience. Fed raw to a
transcription model it returns timings 10+ seconds out.

```
1. Normalise hard first   highpass + compand + loudnorm     ← this is the fix
2. ElevenLabs Scribe, word-level timestamps                  $0.004/min
3. Align script lines to word timings sequentially (script order is authoritative)
4. Never sort cues by timestamp — it reorders dialogue
```

**Tokenise by language.** Scribe returns per-character tokens for Chinese and
per-word tokens for English; comparing letters to words matches nothing and yields
an empty subtitle file with no error.

→ `references/postproduction.md`

---

## Deliverables

- **`-movflags +faststart` or the video looks broken.** `moov` at the end of the
  file means a browser downloads the whole thing before showing a frame. Local
  players do not care, so this never appears in testing. Remux, don't re-encode.
- **Host the file and send a link.** Gmail caps at 25 MB and needs an uploaded
  object anyway; the CDN upload endpoint returns a public URL and caps at ~50 MB,
  so ship a CRF 23 copy alongside the master.
- **Name cards must be opt-in.** A fallback that returned a default set burned one
  film's character names into two unrelated films.

→ `references/delivery.md`

---

## Cost

Measured from `GET /billing/spend/daily`, far more reliable than reasoning about
list prices — a naive estimate said $12.85/shot where the real figure was $3.01.

| Operation | Measured |
|---|---|
| `seedance-2.5/reference-to-video` 1080p 21:9 | ~$0.45/s |
| `seedance-2.0-fast/reference-to-video` | ~$0.83/shot |
| `minimax/minimax-music-3.0` (`is_instrumental: true`) | cheap; ~105 s per call, no duration control |
| `eleven-scribe/transcription` | $0.004/min |

A 150s film is ~$65 before reruns. **Explore with the cheap models, finalise with
the expensive one.** Concurrency is capped at 20 jobs in flight — exceeding it
returns 429 on *uploads* too, which is a confusing way to discover it.

`bytedance/seed-audio-1.0/text-to-audio` exists but is a TTS/dialogue model;
instrumental-music prompts are rejected by its speech safety audit. Use MiniMax.
Model discovery: `GET /catalog/apis` — the published `llms.txt` index is incomplete.

---

## Variants are cheap

- **Alternate ending** — override only the shots that change. 3 of 11 ≈ $16.
- **Another language** — reuse every shot design (already in English), swap only
  `dialogue` and the casting names.
- **Re-mix, re-subtitle, re-grade** — free.

---

## Working practice

- **Do not invent constraints the user did not set.** Three rounds were burned
  forcing horizontal calligraphy to "match the previous film" when vertical is the
  correct convention and the real defect was a petal covering a character.
- **When a complaint is directional, confirm the direction.** "There are several
  people on the boat" was a bug report; it was read as a request, and a cycle was
  spent adding extras.
- **Show a test before committing a batch.** Any new face, any new age variant: one
  render, cropped, approved, then spend.
- **Never write a shell wait-loop that greps for your own command.** `pgrep -f
  "generate.py"` matches the wrapper shell running the loop, so it waits forever and
  the queued work never starts. Cost three separate stalls. Use your harness's
  background mechanism instead.
- **Lint before you spend.** `check_script.py` catches the music ban, casting on empty
  plates, missing shot-design elements, frozen frames and dialogue over-packing — all
  of which are cheap to fix on paper and expensive to fix in a render.

---

## Rights

- Source only from public domain, historical events, or genre archetypes with
  original characters and original dialogue.
- **Do not use a real public figure's likeness** as a reference image. Generate an
  original character instead — it works, and it has carried a billionaire, a
  monk-warrior and a background client across three films.
- **Not-showing is a craft tool, not just a constraint.** An antagonist as a gloved
  hand and a shadow, a president as a cuff and a handshake, a dying father as a
  cough behind a screen — each is stronger than showing the face, and each keeps
  the camera on the protagonist.
- Do not dramatise live litigation or unproven allegations about named real people.
  Swapping the faces does not change what the text is about.

---

## References

- `references/identity.md` — **read this first**; faces, references, priors, swaps
- `references/story.md` — object, promise, rhyming shot, visual grammar, endings
- `references/prompting.md` — prompt anatomy, copy-ready blocks, failure catalogue
- `references/postproduction.md` — subtitles, transitions, mixing, ffmpeg traps
- `references/delivery.md` — encoding, hosting, email, faststart
- `templates/` — `shots_template.py`, `check_script.py`, `generate.py`,
  `audit_faces.py`, `finish.py`
- `examples/last-run/` — a complete 7-shot worked example
