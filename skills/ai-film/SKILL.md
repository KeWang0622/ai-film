---
name: ai-film
description: Produce multi-shot narrative short films (60–240s) with AI video generation — story architecture, shot design, locking a real person's face across dozens of shots, dialogue, transitions, black-and-white and period looks, subtitles timed from audio, and multi-language/multi-ending variants. Use when asked to make a short film, movie, remake, cinematic video, trailer, or any multi-scene narrative video with recurring characters. Also use when an existing AI video looks "not cinematic", when a viewer says they can't follow the story, when characters drift or get swapped between shots, when someone's face stops looking like them, when props or wardrobe change between scenes, when a transition swallows a line, when "black and white" comes back in colour, or when a finished video won't play in a browser.
---

# AI Film Production

Build a narrative short from a premise. Two stages: **generation** (paid, slow) and
**post-production** (free, fast, endlessly re-runnable). Keeping them in separate
scripts is the most important structural decision here — transitions, grading,
loudness, subtitles and delivery get re-run dozens of times without spending again.

```
shots_<project>.py   scenes: shot design, identity, props, audio rules, dialogue
check_script.py      lints the script; --script prints the dialogue alone      free
generate.py          → out_<project>/*.mp4  via pika_client.py (stdlib only)    paid
audit_faces.py       → audit_<project>/*.png   face contact sheets              free
finish.py            → concat → grade → (subtitles) → (score) → cut             free
verify_film.py       measures the cut: runtime, colour, music leak, banding     free
deliver.py           → MASTER / full / share, two-pass linear loudness          free
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
| A second pistol appeared in a stand-off | n/a | fixed — "EXACTLY ONE revolver, the one in her two hands" instead of placing it "low in the corner of frame" |
| A destroyed room came back barely scuffed | "comprehensively destroyed" | better — "the room is ALREADY a wreck in the first frame" |

Negatives still earn their place for *iconography* ("no opera makeup", "no fur on
the face") — they suppress a strong prior. They are near-useless for composition,
staging and headcount.

---

## Order of work

1. **Story first.** Premise → 8–19 scenes, four acts, uneven durations. Pick the
   recurring object and the spoken promise, and **write the causal chain as a list
   of facts** before any shot design. → `references/story.md`
2. **Check the subject for identity risk** (see below). This decides how much of
   your budget goes to reruns.
3. **Reference photos.** Real photos, clean background, face large. Two per person
   at different angles is best; one clean frontal photo can hold. →
   `references/identity.md`
4. **Write `shots_*.py`.** Six design elements per shot; dialogue carries all plot.
   → `references/prompting.md`
5. **Audit it as a stranger.** `check_script.py --script` prints only what the
   audience hears. Read it top to bottom as someone who has never heard of the film.
6. **Generate ONE shot with each new face and look at it — cropped, front-on.**
   A profile test frame cannot verify anything.
7. **Generate the rest**, then iterate freely in post.
8. **Verify by measurement, not by glance.** Face crops beside the reference;
   `verify_film.py` for everything else. Exit code 0 means nothing here.

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
| A 1942 Hollywood romance remade with two leads in their seventies | 2 of 17 first-pass shots rerun for face drift (small face; a prop holding focus); every later rerun was story, staging or wardrobe |
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
   is carried by wardrobe, props, hair and set. A flashback to the leads' youth is
   shot **without faces** — hands, objects, weather — rather than de-aged.
4. **Lock identity with hardware that exists in the photo.** Glasses *shape* (square
   vs round vs oval) is the most reliable discriminator found. Build, height and face
   shape are not — they fool you in profile and in low light.
5. **A recurring prop needs a fixed description block, exactly like a character.**
   "A small notebook" yields a different notebook every scene and the object's
   three-beat silently breaks.
6. **Three simultaneous demands per shot, maximum.** Ask for five and the model
   does the cheapest one.
7. **Never let the video model score the film.** It composes music, the music trips
   copyright moderation, and the job fails *after* rendering — you pay, you get
   nothing. Ban it in every prompt; score in post, if at all.
8. **Title and end cards must be declared `ABSOLUTELY SILENT`.** With no dialogue
   the model invents ambience or music and trips the same copyright filter.
9. **Max three speakers and five lines per shot.** Beyond that the model loses the
   turn-taking and has two characters say the same line in unison. Add an explicit
   one-speaker-per-line rule to the global audio block.
10. **Adding to a prompt weakens what is already in it.** A long new prop block let
    Christmas wardrobe back in; a focal-plane block added to a stand-off dropped
    both leads' costumes. After lengthening a prompt, re-verify what previously
    passed, and restate wardrobe inside the shot as continuity.
11. **`provider_timeout` is not a content problem.** A ~20-minute server ceiling,
    driven by queue load, not shot complexity. It bills nothing. Retry unchanged.
12. **Never use a negative for headcount or framing.** Define the frame so the wrong
    answer has nowhere to live — and that applies to props: place a weapon by whose
    hands hold it, never by its position in frame.
13. **One generation is one image.** A drift across four subjects ("a series of
    tight framings… up the sleeve… out to the platform") came back as a dark blur,
    twice, in two films. Rewrite as one sustained image with one move.
14. **Transitions are picture-only.** A dip to black fades the image; sound carries
    straight through. A line was measured starting at 0.00s of the shot after a dip;
    in a controlled test the old 0.35s audio fade took 17 dB off its first syllable.

---

## A first-time viewer is the only audience that matters

A remake passed every check — faces, colour, sync, lint — and still lost its
audience. "If I'm watching this for the first time I don't know what's going on."
Every break was missing **spoken** information:

| Break | Fix |
|---|---|
| A flashback's city was first named **five shots after** the flashback | name it in the scene that leads into it |
| The heroine's name was **never spoken** in 3.5 minutes; the hero's, four times | name every lead aloud, early |
| The rule of the world (no one leaves without papers) was never stated | say it — it is why the whole plot matters |
| The ending moved **three people on two travel permits** | count the resource out loud at the climax; plant the exception in the first half |
| A time jump (night to dawn, one city to another) happened on a hard cut | dip to black at every jump in time or place |

The method, all free:

```
1. List the facts a stranger needs, each with the line that says it:
       CAUSAL_CHAIN = [("nobody leaves without papers", "nobody leaves this city"), …]
   check_script.py errors on any fact nobody speaks.
2. check_script.py --script   → read only the dialogue, top to bottom, as a stranger.
3. Count every countable thing: tickets, seats, doses, bullets, letters.
   Viewers do this arithmetic whether you meant them to or not.
```

**When a viewer says they are confused, it is a script defect, not a taste note.**
Do not re-grade or re-time it; find the fact nobody said. → `references/story.md`

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

`audit_faces.py` does the contact sheets. Look at **three frames per shot** (15%,
50%, 85%), never one: a single mid-frame once read as "side by side" for a shot
that was correctly back to back, and "no fight" for a shot where the table went over.

Then measure the cut — `verify_film.py`:

| Check | How | What it has caught |
|---|---|---|
| Runtime | cut vs sum of **real** clip durations | concat truncation that exits 0 |
| Colour | 95th-percentile chroma, never the mean | "black and white" shots in full colour; the mean hid them |
| Music | spectral concentration per clip | a model-composed score under a music ban |
| Banding | flat runs on gradients, skipping black frames | a false 1,663 px "band" that was a dip to black |
| Wardrobe | mean brightness of a costume region per shot | a white dinner jacket that went dark (15 vs 128) |

**A measurement that cannot be computed is a failure, not a pass.** A probe once
returned −1 for every clip because its parser matched nothing, and the table read
like a clean bill of health.

---

## Subtitles: time them from the audio

Generated dialogue often sits at −37 dBFS under ambience. Fed raw to a
transcription model it returns timings 10+ seconds out.

```
1. Normalise hard first   highpass + compand + loudnorm     ← this is the fix
2. ElevenLabs Scribe, word-level timestamps                  USD 0.004/min
3. Align script lines to word timings sequentially (script order is authoritative)
4. Never sort cues by timestamp — it reorders dialogue
```

**Tokenise by language.** Scribe returns per-character tokens for Chinese and
per-word tokens for English; comparing letters to words matches nothing and yields
an empty subtitle file with no error.

→ `references/postproduction.md`

---

## Look, sound and delivery

- **Black and white is demanded in the prompt AND forced in post** (`MONOCHROME =
  True`): panchromatic channel mix plus a silver-gelatin curve, not `hue=s=0`.
- **Grain goes on in post** (`GRAIN = 5`), uniform across every cut, and every
  grainy master encodes with **`-tune grain`** — otherwise x264 smooths the grain
  and the banding it hid comes back.
- **Loudness is two-pass linear.** Single-pass `loudnorm` is a compressor: measured,
  it lifted a silent title card from −65 to −16 dBFS and collapsed a 36 dB gap to
  4 dB in a controlled test (on a real film: title at −17 dBFS single-pass, −42
  linear). `deliver.py` measures, then applies one constant gain.
- **Default to no score for dialogue-driven shorts** (`SCORE = False`). A viewer
  rejected a sidechain-ducked orchestral bed as competing with the lines, even with
  speech holding 70–80% of the spectrum. Ask before scoring.
- **`-movflags +faststart` or the video looks broken** in a browser. Remux, don't
  re-encode.
- **Three tiers**: MASTER (video stream-copied, first generation), full-resolution
  CRF 19 for watching, and a 720p share copy stepped down to fit a size cap. Chat
  and upload tools cap attachments (25–50 MB is common), so size the share tier to
  the channel. Never upscale.
- **Name cards must be opt-in.** A fallback that returned a default set burned one
  film's character names into two unrelated films.

→ `references/delivery.md`

---

## Setup and access

`PIKA_API_KEY` in the environment or a `.env.local` beside the scripts (chmod 600,
never committed). Endpoints and field names come from the published index at
`https://dev.pika.art/llms.txt` — read the linked per-model spec rather than
guessing; the aspect field is `ratio`, not `aspect_ratio`.

When nothing renders, the status says why, and the three look alike from a distance:

| Response | Meaning |
|---|---|
| `401` | key unknown or malformed |
| `403 "Your API key is not active"` | key exists but was deactivated |
| `caller_plan_required` | key works; the plan does not include that model |
| `422` | payload rejected — often a prompt over 15,000 characters |

An `ImportError` in the wrapper script hides all four. One pipeline died importing
a client library that had been deleted, which masked both a deactivated key and a
plan that no longer included video models — two separate problems behind one
traceback.

---

## Cost

Read spend from job billing records, never from list prices — a naive estimate once
read 4× high.

| Operation | Measured |
|---|---|
| `seedance-2.5` reference- or text-to-video, 1080p, 4:3 and 21:9 | **USD 0.46/s** (0.457–0.460 across 60+ renders) |
| `seedance-2.0-fast/reference-to-video` | ~USD 0.83/shot |
| `minimax/minimax-music-3.0` (`is_instrumental: true`) | USD 0.09/call; ~105–170 s, no duration control |
| `eleven-scribe/transcription` | USD 0.004/min |

A 200-second film is ~USD 92 before reruns. Iteration on two remakes added 24% and
133% — the second because the story was rewritten twice after a viewing. Budget at
least one full second pass. Concurrency is capped at 20 jobs in
flight — exceeding it returns 429 on *uploads* too.

`bytedance/seed-audio-1.0/text-to-audio` is a TTS model; instrumental prompts are
rejected by its speech safety audit. Model discovery: `GET /catalog/apis`.

---

## Variants are cheap

- **Alternate ending** — override only the shots that change. 3 of 11 ≈ USD 16.
- **Another language** — reuse every shot design (already in English), swap only
  `dialogue` and the casting names.
- **Re-grade, re-time, re-mix, re-deliver** — free.

---

## Working practice

- **Do not invent constraints the user did not set.** Three rounds were burned
  forcing horizontal calligraphy to "match the previous film" when vertical is the
  correct convention and the real defect was a petal covering a character.
- **When a complaint is directional, confirm the direction.** "There are several
  people on the boat" was a bug report; it was read as a request.
- **Show a test before committing a batch.** Any new face: one render, cropped,
  front-on, approved, then spend.
- **Gate every render on the patch having landed.** A prompt patch aborted on a
  failed assertion, wrote nothing, and three shots were rendered — and paid for —
  without the fix. Grep the built prompt for the new text before submitting.
- **Keep rejected takes.** Move them aside rather than overwriting; the old take is
  the evidence for why the prompt changed. `generate.py` skips clips that exist.
- **Never write a shell wait-loop that greps for your own command.** `pgrep -f
  "generate.py"` matches the wrapper shell running the loop, so it waits forever.
  Use your harness's background mechanism instead.
- **Lint before you spend.** `check_script.py` catches the music ban, the 15,000-char
  prompt cap, casting on empty plates, missing shot-design elements, montages inside
  one generation, weapons without a headcount, and unspoken causal facts.
- **No dollar-sign figures in this file.** When the skill is invoked with arguments,
  a dollar sign followed by a digit is treated as a positional placeholder and
  replaced by a word of the user's request — every price here once rendered as the
  name of the film being made. Write `USD 0.45`.

---

## Rights

- **Do not use a real public figure's likeness** as a reference image. Generate an
  original character instead. Real private people from photos they supplied are
  fine — say once that you are assuming consent for the photos you were given.
- Genre premises, historical events and plot *ideas* are not protected; titles and
  short phrases are not copyrightable. **Extended dialogue and specific written
  scenes are.** A remake keeps the beats and the iconography, quotes at most a
  famous short line or two, and writes every other line fresh. Treat public
  distribution of a close remake with more care than a private one.
- **Not-showing is a craft tool, not just a constraint.** An antagonist as a gloved
  hand, a husband as a hand on a shoulder and a hat on a chair, a therapist as a
  voice behind the lens — each is stronger than showing the face, and each is one
  fewer likeness to hold.
- Do not dramatise live litigation or unproven allegations about named real people.
  Swapping the faces does not change what the text is about.

---

## References

- `references/identity.md` — **read this first**; faces, references, priors, swaps
- `references/story.md` — object, promise, rhyme, the stranger audit, endings
- `references/prompting.md` — prompt anatomy, copy-ready blocks, failure catalogue
- `references/postproduction.md` — transitions, grading, loudness, subtitles, ffmpeg traps
- `references/delivery.md` — tiers, encoding, hosting, faststart
- `templates/` — `shots_template.py`, `check_script.py`, `pika_client.py`,
  `generate.py`, `audit_faces.py`, `finish.py`, `verify_film.py`, `deliver.py`
- `examples/last-run/` — a complete 7-shot worked example
