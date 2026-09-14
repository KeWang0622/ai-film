# Prompt anatomy

Every shot's prompt is assembled from five blocks, in this order:

```
ACTION      this shot's design + staging (per shot)
CASTING     who is in it — OR the empty-plate block (per shot, conditional)
LOOK        photographic texture (global)
AUDIO_RULE  performance + the music ban (global)
DIALOGUE    the lines, with delivery direction (per shot)
```

Assemble per-shot in code, not by hand:

```python
def build_prompt(shot: dict) -> str:
    blocks = [shot["action"]]
    blocks.append(IDENTITY if shot.get("cast", True) else NO_CAST)
    blocks += [LOOK, AUDIO_RULE, shot["dialogue"]]
    return "\n\n".join(blocks)
```

The conditional on line 3 is load-bearing. See "empty plates" below.

## ACTION — the six elements

Scene description gets you a stock photo. Shot design gets you a film.

```
SHOT DESIGN — LENS: 200mm long lens, heavy telephoto compression.
FOREGROUND: a rooftop antenna array, very close and thrown far out of focus,
  occupying the bottom-left quarter as a dark silhouette we shoot past.
FRAME: horizon on the LOWER third. The dust wall fills the upper two-thirds.
  One slender tower stands off-centre right, still catching the last direct sun.
MOVE: absolutely locked off. The only motion is the dust front advancing and,
  at the end, swallowing that lit tower.
LIGHT: strong backlight — sun behind the dust, city as layered silhouettes.
ACTION: the dust front rolls over the skyline; street-light grids wink out in
  long successive waves; the lit tower goes dark last.
```

What each element buys:

| Element | Without it |
|---|---|
| LENS | flat middle-distance perspective on everything |
| FOREGROUND | no depth — subjects look pasted onto the background |
| FRAME | subject dead-centre, symmetrical, no negative space |
| BLOCKING | actors stand still and pose instead of doing something |
| EYELINE | **actors look at the lens** — the most anti-cinematic result possible |
| MOVE | either static, or drifting with no motivation |

State *why* the camera moves: "a slow push-in that drifts off the commander and
settles on the two of them — the move transfers the subject, that is its reason."

Add to the global negative list: `subjects standing dead-centre facing the lens;
flat symmetrical postcard compositions with no foreground layer`.

## CASTING — identity that survives eleven shots

```
CASTING — two leads, faces held rigidly consistent with their reference
photographs in every shot (bone structure, eye shape, nose, jawline, hairline):
@Image1 = MAYA, a woman in her late twenties. East Asian. SHE ALWAYS HAS A
  FULL HEAD OF LONG DARK HAIR — never bald, never shaved, never short.
@Image2 = NOAH, a man in his late twenties. East Asian. Thick tousled dark
  hair, THIN METAL-FRAMED RECTANGULAR GLASSES worn in every scene, light stubble.
Husband and wife, both engineers. Play the easy physical familiarity of a long
  marriage.
WARDROBE — unchanged across the film: identical charcoal-grey flight suits,
  faded mission patch on the left shoulder, rust-orange stripe at the cuff.
  Never restyle hair or change clothing between shots.
```

**Hardware anchors carry identity; adjectives do not.** In practice the glasses
and the cuff stripe propagated perfectly across every shot — and the wardrobe
description even unified the uniforms of a crowd of thousands of extras. The
male lead stayed recognisable throughout; the female lead, described only by hair
and brows, drifted noticeably. Give every character at least one hard object.

**Reference photos matter more than any of this.** One photo per person is the
dominant cause of drift. Supply 5–8 per character at different angles and
lighting; `image_urls` accepts up to 30.

## Empty plates

A shot with no cast needs the casting block *removed*, not a negative added.

```python
NO_CAST = (
    "THIS IS AN EMPTY PLATE SHOT — a landscape/vfx plate with NO CAST AT ALL. "
    "There are no actors, no people, no figures, no silhouettes, no faces, no "
    "bodies anywhere in the frame, at any distance, including the far background. "
    "The frame contains only environment, structure, weather and light."
)
```

`Absolutely no human figure in frame` inside a prompt that also carries CASTING
failed three separate times. Strengthening the wording never helped — the two
instructions were fighting, and casting won. Removing CASTING fixed it on the
first attempt.

## AUDIO_RULE

```
AUDIO: spoken <LANGUAGE> dialogue exactly as written, performed with restrained,
sincere, deeply felt emotion — quiet intensity, never shouting or melodramatic.
Natural breath and micro-pauses. Plus diegetic ambience only: <specifics>.
ABSOLUTELY NO music, NO orchestral score, NO singing, NO instruments, NO stings.
```

The music ban is not stylistic. Without it the model composes a score, that score
trips a copyright fingerprint, and the job is rejected **after the video has
finished rendering** — 148s of paid render time, `content_moderation`, no output.
Adding the ban took a batch from 5/6 to 6/6.

## DIALOGUE

Carries **all** plot information. Models cannot render legible on-screen text —
asking a screen to explain the premise produced a chat-app UI full of garbled
glyphs. If the audience must know it, someone says it.

Two-character names *do* render correctly if you ask for them in-frame, but the
size is not controllable and comes out small. Burn names in during post instead.

Write delivery direction inline:

```python
"dialogue": (
    'MAYA, quietly, still watering: "The list came through. …It\'s both of us." '
    'NOAH, after a beat: "Good. I was never going to let you go alone."'
)
```

## Failure catalogue

| Symptom | Cause | Fix |
|---|---|---|
| People appear in a shot meant to be empty | CASTING block present | drop it; define the plate type positively |
| Character goes bald / restyled | abstract adjective ("older, weathered") | list checkable features + block the wrong reading |
| Wardrobe changes colour in one shot | local description overrode the global block | restate wardrobe in that shot's ACTION |
| Only one of several requested beats happens | >3 simultaneous demands | split the shot or cut demands |
| Job fails at `content_moderation` after rendering | model composed a score | add the music ban |
| Garbled text / chat UI in frame | plot info assigned to a screen | move it to dialogue; ban UI in the negatives |
| Everyone faces camera, dead centre | no EYELINE / FRAME | add both; add the composition negatives |
| Two shots look like the same composition | no per-shot LENS/FOREGROUND | differentiate deliberately |
| `provider_timeout: exceeded max lifetime` after ~1205s | server-side ~20 min ceiling; hit by the heaviest shot in a batch | **just retry** — same prompt usually passes (528s vs 1208s observed). Simplify only if it fails twice |
| Reference-photo accessories bleed into the character | the photo's tiara/jewellery/styling carried into an incompatible scene | state the character's condition explicitly in that shot: "no tiara, no jewellery in her hair, hair salt-stiff and dishevelled, coat soaked and stained" |
| A dark, murky blur where a sequence of images was asked for | several subjects or places in one generation ("a series of framings… then finds…") | ONE sustained image, one move; split the rest into shots |
| A second weapon appears | the weapon placed by frame position ("low in the corner of frame") | "EXACTLY ONE revolver, the one in her two hands; no other weapon anywhere in frame" |
| Strangers' faces on the wall | framed photographs requested as set dressing | dress the wall with something that has no face |
| A fight scene comes back as a mild scuffle | destruction described as an event to perform | describe it as a state the shot OPENS in: "already a wreck in the first frame" |
| Attackers read as shoppers | threat written as "distant shapes" | make it legible: weapons up, advancing, still at distance, faces unreadable |
| A monochrome end card measures as colour | a colour word on the card ("cream card") | black field, white letters — monochrome by construction |
| Both leads change costume in one rerun | a longer prompt displaced the wardrobe | restate wardrobe in that shot as "WARDROBE CONTINUITY — unchanged from every other scene" |
| A key line is thrown away | one line of four in a 12 s shot | its own shot, ≤3 lines, silence directed before and after (see story.md) |

---

# Additions from the next ten films

## Describe the scene you want; do not list the things you don't

The single highest-yield correction in this pipeline. Ranked by evidence:

**Headcount.** Three background extras kept appearing on a small boat. Adding
`ABSOLUTELY NO other passengers, NO crowd, NO extras, NO boatman, NO other
travellers, NO figures on the bank — if any additional human figure appears the
shot is wrong` **failed**. The frame was a tight waist-down shot of a bench and
several pairs of legs — the model saw a bench with room on it. Replacing the frame
with

```
A WIDE SHOT THAT SHOWS THE ENTIRE SMALL BOAT FROM BOW TO STERN, so the whole vessel
and everyone in it is visible at once and can be counted. The boat is small — a
two-man river skiff — and there are exactly three people in it and no empty bench
for anybody else. Do NOT frame on laps, knees, hands or a row of seated bodies.
```

worked first try. **Give the wrong answer nowhere to live.**

**Layout.** Calligraphy kept rendering as a vertical column. Two rounds of "not
stacked vertically, not in a column" failed. What eventually mattered was
describing the *physical object*: "a wide landscape strip of paper, much wider than
it is tall, its long edges running horizontally across the frame."

**Wardrobe.** See `identity.md` — the fix is a clean reference photo, not a longer
negative list.

Negatives *are* worth their place for suppressing a strong learned prior: opera
makeup, fur on a face, prosthetics, wire-work, modern objects in a period film.
They are near-useless for composition, staging and headcount.

## Adding to a prompt weakens what is already in it

A long prop-description block was inserted into a shot's action text to fix prop
continuity. The fix worked — and Christmas wardrobe came back through a constraint
that had been holding for the previous three renders. The prompt got longer and the
casting-block negatives lost weight.

Two consequences:

1. **Put load-bearing constraints early and in the action text**, not only in the
   casting block. A global wardrobe rule that must not fail belongs at the head of
   the shot, appended to `action`, not buried after 800 words of look description.
2. **After lengthening a prompt, re-verify what previously passed.** Fixing A
   breaks B, and B was already signed off, so nobody looks at it.

## Dialogue attribution collapses past three speakers

Five people and seven fast overlapping lines in one shot produced two characters
speaking the same line in unison, mouths moving together. Not a rendering artefact
— the model lost the turn-taking.

Fix in two places. Globally:

```
DIALOGUE ATTRIBUTION IS CRITICAL: every line is spoken by exactly ONE person, the
one named in front of it, and only that person's mouth moves on that line.
NOBODY EVER SPEAKS IN UNISON. No two characters say the same words at the same
time. No overlapping dialogue, no chorus, no echo, no doubled voices. Lines are
taken strictly in order, one at a time, with a clear beat between each.
```

And in the shot — cut to four lines, one speaker each, numbered:

```
Only one person speaks at a time. Four lines, strictly in this order, with a clear
pause between each. Nobody speaks in unison.
1. IRIS (young woman, teasing): "You said seven."
2. NORA (older woman, dry): "I am home."
3. MAYA (young woman, to her sister): "Let her sit down."
4. OMAR (large older man, low, sliding a glass of water over): "Eat something."
Nobody else says anything. The rest is laughing, cutlery and chairs.
```

The shorter version is also better writing. Seven lines of crosstalk was a
screenwriter performing "lively family"; four lines and some cutlery is a family.

## Title and end cards must declare silence

A card with no dialogue fails `content_moderation` with *"the output audio may be
related to copyright restrictions"* — with nothing to say, the model composes
ambience or music and trips the filter. Even a card whose dialogue field said
only "no dialogue, very quiet, a loom still sounds in the distance" was enough
to fail it — describing silence is not the same as forbidding sound.

```
"dialogue": ("ABSOLUTELY SILENT. No dialogue, no music, no melody, no instrument, "
             "no song, no rhythm of any kind. Only a faint room tone.")
```

## Empty-plate shots go to text-to-video

`reference-to-video` requires at least one image and returns 422 without one. Route
any shot with no cast to the `text-to-video` endpoint and drop `image_urls`
entirely — do not try to satisfy the endpoint with an unrelated image.

```python
api = "bytedance/seedance-2.5/reference-to-video"
if not payload.get("image_urls"):
    payload.pop("image_urls", None)
    api = "bytedance/seedance-2.5/text-to-video"
```

## Short text renders correctly

The model renders short strings of Chinese and English cleanly — verified with
two-, four- and five-character brush calligraphy, and with handwritten English
lines and short name lists. Earlier garbling was a *volume* problem (a whole UI of
text), not a language problem. Title cards can be pure t2v with no compositing.

Give the layout physically, and keep the text clear of anything that could cover it:

```
FRAME: a sheet of cream xuan paper lying flat on dark wood, camera directly
overhead, dead level, the sheet parallel to the frame edges. Two characters in a
single column, PLACED IN THE EXACT CENTRE with equal empty paper left and right,
correct, complete and entirely unobstructed.
ACTION: one petal drifts down and rests on the BARE PAPER WELL TO THE RIGHT of the
column. IT MUST NOT TOUCH OR COVER EITHER CHARACTER.
```

## Per-shot description overrides

A global character block will fight a scene that needs a change — the film's final
beat was "the circlet is gone", but the character definition said "a thin gold band
on his forehead", and the definition won for three renders.

Support a per-shot override in the casting builder:

```python
override = shot.get("desc_override", {})
lines.append(f"{tags} {verb} {override.get(who, PEOPLE[who])}")
```

Then also fix any *other* block that restates the thing — the anti-swap block was
still saying "the one with the gold band on his forehead" and pulled it straight
back in. Grep the assembled prompt for the attribute you are removing.

---

# Additions from two remakes

## Copy-ready: pacing and a line that must land

```python
KEY_LINE = (
    "PACING - CRITICAL: spoken VERY SLOWLY. A LONG SILENCE of several seconds before "
    "the first line, a clear pause between lines, and a LONG SILENCE after the last "
    "line in which nobody speaks and nobody moves. The silences are as important as "
    "the words. "
    "The line '<LINE>' is the most important line in the film: spoken CLEARLY and "
    "DISTINCTLY, every word fully articulated at normal volume - not muttered, not "
    "rushed, not swallowed at the end. "
)
```

Verify the silence rather than trusting it: speech-band energy in 0.25 s windows
shows where the voice actually is. The first build of a shot with this block measured
3.5 s silent, the line, 4.25 s silent, then two short replies.

## Copy-ready: a setting several shots share

When a sequence spans shots, write the place and the wardrobe as constants and
concatenate them into every shot of the sequence, the same way a prop or a character
gets a block. It keeps the fog, the aeroplane and the hats identical from cut to cut:

```python
AIRFIELD = (
    "THE AIRFIELD: night, thick low fog rolling across a wet concrete apron. A "
    "twin-engine 1940s passenger aeroplane stands a little way off with its propellers "
    "turning and its cabin windows lit, a boarding ladder down and one ground crewman "
    "moving about it at distance. A hangar and a small control tower are dim shapes "
    "behind the fog; a bank of lamps throws hard beams through it. "
)
```

## Unseen characters, written so they stay unseen

A third lead nobody casts costs nothing and holds no likeness. It needs the absence
written as positively as a presence:

```
VIKTOR IS NEVER SEEN: a hand on her shoulder, a dark sleeve, a felt hat on the
chair beside her, and a voice. Never his head, never his face, never his body.
```

The same pattern carried a therapist ("a calm voice from just behind the camera —
never a head, never a shoulder, never a reflection"), a police chief (a uniform
sleeve and a glass at the edge of frame) and a target (a broad silhouette at the far
end of a dock that leaves frame almost at once).

## Title and end cards that read

Rendered text is reliable when the layout is physical and the words are few:

- one or two words, dead centre, equal empty space on every side, "correct, complete
  and entirely unobstructed", "no other writing anywhere in frame";
- a camera move that **ends** locked off on the text — a tilt down a sunlit wall to
  a stencilled sign, a slow track along a bare wall to an engraved brass plate;
- for monochrome films, a black field and white letters rather than a coloured card.

A short name on a brass plate and one word on a stencilled sign both rendered
legibly first time. The failure was elsewhere in the frame: photographs on the same wall.
