# Story architecture

Shot craft makes a film look expensive. These devices make it land. Every film in
this pipeline used all three, and they cost nothing to apply.

## 1. The object

Introduce a small, ordinary, physical thing early. Hand it over at the crisis.
Complete it at the end. Three appearances, no more — a fourth turns it into a
gimmick.

| Film | Object | Introduced | Handed over | Completed |
|---|---|---|---|---|
| Space epic | a potted plant | "we water it together when we get back" | — | she returns to spring alone |
| Period epic | a bracelet with a broken clasp | he mends it through a railing | he presses it into her palm as they part | she fastens it onto **his** wrist |
| Action comedy | a chipped mug | he fills it, she slides it back half-drunk | it sits between them at the loaded dinner | they share it on the porch at dawn |

Why it works: the audience cannot hold an abstraction across 120 seconds, but they
will track an object effortlessly. The object carries the theme so the dialogue
does not have to state it.

Pick something that survives the story physically. The mug surviving a gunfight
that destroys an entire house *is* the ending's argument.

## 2. The promise

A spoken line, established in act one, echoed at the turn, paid off at the end.
Change who says it — that inversion is the whole payoff.

```
ACT 1   she says it to him          "come back and watch the spring with me"
TURN    he gives it back to her     as he is torn away: "watch the spring for me"
END     she completes it alone      "…spring came. This time I watch it for you"
```

Same three beats, happy variant:

```
ACT 1   she says it to him          "both of us, off that ship together"
TURN    he returns it under fire    "you still owe me a walk down a gangway"
END     they say it together        "both of us. Off this ship together."
```

The line must be plain. Anything writerly breaks — it has to survive being spoken
three times.

## 3. The rhyming shot

Shoot two scenes with an *identical* setup — same lens, same framing, same camera
move, same blocking rhythm — separated by the turn. Nothing about the composition
changes; everything about the meaning does.

The action comedy opens on a symmetrical two-shot across a kitchen island in warm
morning light, and returns to exactly that setup at night after both leads know
what the other is. The audience feels the rhyme before they can articulate it.

Write it explicitly in the second shot: *"the exact symmetrical two-shot from
scene 01, same kitchen, same lens, now at night with one pendant lamp. The
composition is identical; everything else has changed."*

## Visual grammar: give the opposition two languages

Find the film's central opposition, then assign each side its own photography.
State the rule in the module docstring so every shot obeys it.

**Period epic — class:**

| | Lens | Composition | Light |
|---|---|---|---|
| Her world (first class) | 100mm, very shallow | symmetrical, frame-within-frame, always boxed in | cold crystal, even, no warmth |
| His world (steerage) | 24mm, deep focus | deliberately unbalanced, low ceilings in shot | warm lamp-yellow from below, deep shadows |
| Together | — | **always an obstacle in the foreground** | — |

**Action comedy — domestic vs operational:**

| | Grammar |
|---|---|
| Home | symmetrical, slow dolly-in, warm and slightly over-lit — shot like a family drama |
| Work | low angle, wide, cold and high-contrast, fast lateral tracking |
| Confrontation | both grammars in one room — that collision is the joke and the theme |

## The barrier ladder

If the film is about two people kept apart, escalate the physical thing between
them, then remove it.

```
railing        first meeting — he mends the clasp through it
locked gate    the flood — the same barrier, now lethal
officer's arm  the lifeboat — human, and final
nothing        dawn on the rescue ship — for the first time, nothing between them
```

Write the final shot's absence explicitly: *"for the first time in the film there
is NOTHING between them: no railing, no gate, no officer's arm, no crowd."*
Models respond to that.

## Structure

Four acts, uneven durations. Uniform shot lengths read like slides.

The classical East Asian four-act shape (qǐ-chéng-zhuǎn-hé) fits short films better
than three-act structure, because it gives the turn its own act rather than burying
it inside a long middle:

```
起 qǐ    setup       ~25%   who they are, what they have, what threatens it
承 chéng journey     ~27%   the world opens; the promise is made
转 zhuǎn crisis      ~30%   the cost is revealed; the object changes hands
合 hé    resolution  ~18%   payoff — the shortest act, and it should feel short
```

An 11-shot / 120s example: `14, 8, 8 | 12, 10, 10 | 12, 14, 10 | 10, 12`.

Two structural shots earn their place in almost every film:

- **A cold open with no faces.** Hands, an object, a landscape. Establishes tone
  and stakes before the audience has anyone to attach to.
- **A silent beat after the crisis.** No dialogue at all, held past comfort. Going
  straight from catastrophe to resolution feels rushed; grief and relief both need
  a moment to be absorbed.

## Dialogue

Carries **all** plot information — models cannot render legible on-screen text.
Every plot fact must be spoken by someone.

Test the causal chain by writing it as a sentence with no gaps:

> Earth is dying → the only habitable world is beyond the gate → the fleet cannot
> cross without a beacon → they go to plant it → he is lost doing it → the fleet
> crosses → she returns to a healed Earth.

If any arrow is not spoken aloud somewhere in the film, the audience will not have
it. An early draft skipped "what is the mission for" entirely and the whole middle
read as beautiful nonsense.

## Working with real people and existing IP

- Genre premises, historical events and plot ideas are free to use: a shipwreck, a
  class divide, spies married to each other, time dilation. Titles and short
  phrases are not copyrightable. Extended dialogue and specific written scenes are.
- For an original film, write original characters, beats, dialogue and recurring
  object, and state that in the module docstring so it stays true as the script
  evolves.
- For a remake, keep the beats and the iconography, quote at most a famous short
  line or two, and write every other line fresh. See "Remakes" below.
- When the leads are real people from supplied photos, assume consent for the
  photos you were given and say so once — do not build likenesses of people who
  did not supply them.

---

# Additions from the next ten films

## Props need a description block, exactly like characters

The object only works if the audience recognises it as *the same object*. Writing
"a small notebook" produced a different notebook in every scene — a legal pad, a
spiral pad, a hardback — and the three-beat silently broke. Nobody notices the
break; they just stop feeling the ending.

Give the prop a constant, the way you give a character one:

```python
NOTEBOOK = (
    "THE NOTEBOOK — the single most important prop in the film, and it must look "
    "IDENTICAL in every shot it appears in: a SMALL POCKET-SIZED notebook, soft "
    "TAN-CREAM leatherette cover, rounded worn corners, a dark elastic band around "
    "it, cream unlined pages densely filled with small handwritten notes. "
    "It is NOT a legal pad, NOT a spiral notebook, NOT a hardback. It gets more "
    "battered as the years pass but it is always the same object. "
)
```

Then concatenate it into every shot that uses it. Include the wear rule — "more
battered, same object" — or continuity reads as a replacement.

A detail that survives is worth more than a detail that is described: armour with
**two plates missing from the left shoulder, never replaced** for twelve years does
more work than any amount of "battered".

## Two parallel three-beats that converge

One tragic, one comic, sharing a final frame. Better than either alone.

```
TRAGIC (the jade)     thrown down at the first meeting
                      still round his neck when the veil lifts and it is the wrong bride
                      laid on her grave in the snow

COMIC (a bad poem)    recited to a silent room; he is delighted with it
                      revised, worse, recited to a man too broken to hear it
                      still being revised in the snow — he looks up at the empty
                      ground and says "…the flowers are gone." Then, pleased:
                      "That line is good."
```

The comic line lands the tragedy. He says the whole film in five words and does not
know it. **The comic character must never be in the tragic scenes as relief** —
keep the two lines apart until the final shot, or both are ruined.

## The ending needs its own scene

Stopping inside the last dramatic scene reads as *a scene ended*, not *a film
ended*. Add a short, quiet coda after the climax with its own frame.

A coda works best when it **inverts the title or the premise**:

- Film called *The Word for It*, about a woman who could never name what she was.
  Coda: she writes four names in the notebook. "That's not a word." "No. There
  isn't one for that."
- Comedy about a man doing stupid things. Coda: "You know the rabbit isn't coming
  back." "I know." "Then what are you waiting for?" "…While I wait, you come and
  sit with me." Every earlier joke re-reads as loneliness.

Bookend the coda with the opening image — same table, same lamp, same framing,
reversed camera move. A title card and an end card on the same sheet of paper, with
a petal landing in the opening and a snowflake landing in the *same spot* at the
end, closes the film's central image without a word.

## Not showing is a tool

An unseen character is often stronger than a cast one, and it dodges likeness
problems for free:

| Character | How they appear | Effect |
|---|---|---|
| The warlord tempting the hero | a gloved hand pouring wine, a shadow across the floor | he is a pressure, not a person |
| The president giving an award | a cuff, a handshake, a shoulder leaving frame | the camera never leaves the protagonist |
| The dying father | a cough behind a paper screen, an unfocused silhouette, armour he can no longer wear | no line of dialogue needed to justify her leaving |

In the last case the screen is folded away and the space behind it is empty in the
final scene, and **nobody remarks on it**. Withholding is also how you handle grief
without a speech.

## Design docs and shot text must agree

A rhyming shot was specified in the module docstring and never written into the
shot body. The generator reads the body. The film shipped with a B-side and no
A-side — the payoff pointed at nothing.

Anything structural — rhyme, object beat, promise beat — must appear **in the shot
that has to carry it**, not only in the plan. Grep the built prompt to prove it.

## Comedy: play it straight

All of it comes from *he means it* against *the room has nothing to say back*.

```
PERFORMANCE — CRITICAL: he is COMPLETELY SINCERE at all times and has no idea he is
being foolish. He never mugs, never pulls faces, never plays to camera, never
winks. He does absurd things with total concentration and quiet satisfaction, the
way a man does something he is certain is correct.

The others' reactions are TINY. They watch, they do not intervene, they do not roll
their eyes. At most one stops what he is doing for a beat and then goes back to it.
```

Ban slapstick in the global look block: `slapstick mugging, cartoonish expressions,
exaggerated pratfalls, sped-up motion, comic sound-effect faces`.

Shoot the comedy like a serious film — the same camera grammar as the drama. A
locked-off symmetrical wide of one man labouring while another sits in perfect
contentment beside a tree stump *is* the joke. Length is the joke too: hold the
shot of him carefully carving a notch into the boat's rail long past comfortable.

## Rhyming shots: what actually has to match

Not "similar" — identical setup. Distance, height, lens, composition, the position
of the object in frame, the direction of the camera move.

| Film | A | B |
|---|---|---|
| Brotherhood epic | three kneeling in an orchard, petals falling, warm, handheld arc | three kneeling in a courtyard, snow falling in the same part of frame, cold, same arc |
| Immigrant drama | a nurse at a hospital corridor window at night, city outside, writing in a notebook standing up | the same woman at her own firm's window at night, same position in frame, same notebook |
| Ballad | a loom in a dark room, one oil lamp, the shuttle stops mid-pass | the same loom, same lamp, same framing, the shuttle starts again; the armour is back on its peg |

Falling things rhyme especially well: blossom → snow, and the paper cards that open
and close the film can carry the same pair.

---

# Additions from two remakes and a recut

## The stranger audit

A remake passed every technical check and still lost its audience: *"If I'm
watching this for the first time, I don't know what's going on."* The fix was not
in the pictures. Every break was a fact nobody said out loud.

| What a first-time viewer hit | What was missing |
|---|---|
| Hands on a café table in the rain — whose, where, when? | The flashback's city was first named **five shots after** the flashback |
| Who is she? | The heroine's name was **never spoken** in the whole film; the hero's, four times |
| Why do these papers matter? | Nobody ever said you cannot leave the city without them |
| Wait — how did he get on the plane? | Three people left on **two** travel permits |
| Did we skip something? | Night-to-dawn and airfield-to-another-country happened on hard cuts |

Run it every time, before rendering and again after the first cut:

```
1. Write CAUSAL_CHAIN in the shot script: every fact a stranger needs, paired with
   the phrase that says it. check_script.py errors on a fact nobody speaks.
2. check_script.py --script — read ONLY the dialogue, top to bottom, cold.
3. Name every lead aloud in the first third.
4. Name the place and time of a flashback in the scene that leads INTO it.
5. Dip to black at every jump in time or place; hard cut only inside a scene.
```

When a viewer says they are confused, do not re-time, re-grade or add music. Find
the fact nobody said, and have somebody say it.

## Count the resources out loud

If the plot turns on something countable — tickets, seats, doses, letters, bullets —
the audience does the arithmetic whether you meant them to or not. The climax of one
remake handed out two travel permits and then put three people on the aeroplane. It
read as *"what the heck?"*, not as romance.

The repair has three parts, and all three have to be spoken:

```
ASSIGN     at the climax, say whose each one is
           "Two letters. This one is yours. This one is hers."
ASK        let a character voice the audience's question
           "There were only ever two. You haven't got anything."
ANSWER     with something planted in the first half
           "I've had my own exit visa in a drawer for two years."
PLANT      (mid-film)  "You could have left this city any time in eight years."
                       "And gone where?"
```

The plant is what stops the answer feeling like a cheat — and here it deepened the
character: he never lacked a way out, only somewhere to go.

## Remakes: a happy ending on a tragic source

When the source ends in renunciation and the brief is a happy ending, do not delete
the sacrifice — it is usually why the source is loved. **Move it to another
character.** In one remake the husband, not the hero, gives up his claim, and does
it as an unseen voice, a hand and a hat.

Then **recount the logistics**, because moving the sacrifice changes who needs what.
That recount is exactly where the three-people-on-two-permits hole came from.

Keep the source's visual signature where the audience will look for it: the fog, the
aeroplane with its propellers turning, the trench coat and the hat pushed back off
the face. Invert only the outcome. A remake that keeps the staging and changes the
ending reads as homage; one that changes the staging reads as a different film.

## The line the film is remembered for needs its own shot

A famous line placed fourth among four lines in a 12-second shot went by in a second
and a half. The viewer: *"Too fast, too short, gone before it lands."*

Give it a dedicated shot: the tightest framing in the film, at most three lines, and
direct the silence explicitly — "a LONG SILENCE of several seconds before the first
line … a LONG SILENCE after the last". Measured on the rebuilt shot: **3.5 s of
silence, the line, 4.25 s of silence** — 73% of the shot without speech. Then make
the next lines *about* the line ("You said that to me in Paris." / "I meant it in
Paris.") so the film itself points at it.

Plant it earlier too, where the source does. A line heard once is dialogue; heard a
second time, in a different place, it is a theme.

## A flashback without faces must be anchored before it starts

Shooting the leads' past as hands, glasses and rain avoids de-aging and looks
beautiful — and on its own it reads as nothing at all. The scene before it has to
name the place and the time ("Eight years." / "Eight years since Paris."), and the
flashback's own lines should name the place again. After that fix the same images
read instantly as memory.

## Comedy of a long marriage: make the number big

A spy-marriage comedy recast with leads in their seventies changed "married five or
six years" to **forty-one**. It is funnier and it hurts more: four decades of
answering "How was your day?" with a lie. Ageing the premise to fit the actors
beats ageing the actors to fit the premise, every time.
