# Identity: keeping a real person's face across a whole film

The hardest problem in this pipeline, and the source of nearly every rerun. Ten
films' worth of failures, grouped by cause.

---

## 1. The reference photograph is the whole game

### Real photos beat generated ones

A generated reference stacks the image model's own bias on top of the person. Use a
real photograph whenever one exists. Only generate a reference when every real
photo is unusable (e.g. the person is wearing a Santa hat in all of them), and then
generate it *from* the real photo with instructions to change only clothing and
background.

### Two photos beat one, badly

A single wide photo where the face occupies a small part of the frame degrades into
a *type* — "a bald bearded older white man" instead of the actual person. Supplying
two real photos at different angles and lighting fixed it immediately.

```python
refs["zac_real"] = [close_portrait_url, group_photo_crop_url]
# casting block emits: "@Image1, @Image2 are ALL THE SAME PERSON: ..."
```

The endpoint accepts up to 30 images. There is no reason to give it one.

### Whatever is in the photo will leak into the film

Verified across four separate projects:

| In the reference | Leaked into |
|---|---|
| Rhinestone tiara + pearls (formal portrait) | a Tang-dynasty monk, a Han-dynasty general, a shipwreck at dawn |
| Santa hat + orange scarf | a 3 a.m. kitchen during law school |
| Red snowflake sweater | a present-day family dinner |
| Red festive clothing | a Northern Wei army camp |

**The fix is a clean reference photo, not a longer negative list.** Negatives hold
until the prompt grows, then fail silently. Generate a plain-background,
plain-clothing version of the person and use that as the anchor:

```
The SAME WOMAN as in the reference photograph, identical face, identical age,
identical hair — change ONLY her clothing and remove her hat. Plain grey crew-neck
sweater. Her head is BARE. Plain seamless light grey studio background, even soft
frontal lighting. Photorealistic passport-style portrait, 85mm, natural skin
texture, no retouching.
```

Keep the original as `alt-`, keep the clean one as `PRIMARY`.

---

## 2. Never age a face

Corrected three times in one project before it stuck: young lead, young husband,
teenage daughters. Every de-aged or aged-up render lost the person.

**Rule: one photograph per person for the entire film, every era.** The passage of
time is carried entirely by:

- hairstyle (loose → pinned → bound under a cap)
- wardrobe (hospital scrubs → cheap blazer → good suit)
- props and technology (CRT monitors and payphones → flat screens)
- set dressing, weather, and how the person moves

Write it into the character block explicitly, or the model will "help":

```
SHE LOOKS EXACTLY AS SHE DOES IN HER REFERENCE PHOTOGRAPH — do not make her
younger, do not smooth her skin, do not change her face in any way. Only her hair
and clothes place her in 2000.
```

And in the global look block:

```
PERIOD IS CARRIED BY THE WORLD, NOT BY THE FACES. Do NOT age or de-age any actor's
face away from their reference photograph to signal the passage of time.
```

The same applies to disguise. A woman disguised as a soldier must not have her face
masculinised — the disguise is hair, cap, grime and posture. If the face changes,
the audience loses the only thing that makes the story work.

---

## 3. Adjectives override the `@ImageN` tag

**The most expensive single bug found.** Two young men of similar age were
described as:

```
SECOND BROTHER — a lean, tall young man …          (photo: rounder, wider face)
THIRD BROTHER  — a heavy-set man, round open face … (photo: longer, narrower face)
```

The descriptions contradicted the photographs. The model followed the **adjectives**
and swapped the two actors for the entire film — one wore the other's costume in
every shared frame. Twelve shots, eight reruns.

### The rules that come out of it

**Never write a physical attribute that contradicts the photo.** If the character
"should" be burly and the actor is slim, the costume carries it, not the face:

```
His bulk comes entirely from his heavy armour and fur collar, never from altering
his face.
```

**Distinguish by hardware that is actually in the photograph.** Ranked by
reliability:

1. **Glasses shape** — square/rectangular vs perfectly round. Near-perfect.
2. A single distinctive garment in a colour nobody else wears (deep red cloak).
3. A carried object (a specific blade, a spear, a staff).
4. Height *stated as a relation* ("a full head taller than her"), not as a number.
5. ~~Build, face shape, "lean", "heavy"~~ — never. This is what caused the swap.

**Write an explicit anti-swap block** for any two same-gender, same-age-bracket
characters sharing a frame:

```
X AND Y MUST NEVER BE SWAPPED. Assign them strictly by their own tagged photographs
and by these markers, and do NOT reassign them based on build or face shape:
X wears SQUARE rectangular spectacles and a deep green cloak;
Y wears ROUND circular spectacles and a fur-trimmed collar.
Check both in every shared frame.
```

---

## 4. Famous characters overwrite faces

Replacing the *name* is not enough. Verified twice, expensively.

**Monkey King.** Every occurrence of the name was removed from prompts and dialogue
(characters addressed him by role instead). The actor's face was still buried under
monkey prosthetics. The cause was the **whole iconography** — tiger-skin kilt, gold
armour, gold circlet, pilgrimage company, the monk in frame. Together they summon
the makeup with or without the name. Only stripping the costume to a plain hemp
tunic recovered the face.

**Guan Yu.** The jujube-red face, the five-strand beard, phoenix eyes and green robe
are the hardest prior in the Chinese canon. Stripped to a green cloak and a blade;
the face survived. He no longer reads instantly as the character — that is the
trade, and it is the right one when the brief is "these three people".

### Procedure for a high-prior character

1. Remove the proper noun everywhere, including dialogue — use relational address
   ("elder brother", "the master"). Grep the built prompt to confirm zero hits.
2. Remove the **entire signature costume**, not the name only.
3. Keep exactly one or two iconic props as identity anchors (the blade, the staff).
4. Add explicit negatives for the makeup itself — this is where negatives *do*
   work: `ABSOLUTELY NO opera makeup, NO painted red face, NO fur on the face, NO
   prosthetics, NO stage mask.`
5. Tell the user the character will not look canonical, and why.

---

## 5. What the shot itself does to identity

Identity holds when **the face is large, sharp, and in one continuous setup.** It
drifts when any of those fails.

| Shot property | Effect |
|---|---|
| Multiple hard cuts inside one generation | **Severe.** Re-anchors at each cut and loses the photo. Rewrite as one unbroken move. |
| Wide action with whip-pans, faces small, motion blur | Severe. Use a moving master at 35–40 mm with one face always large in foreground. |
| A prop in sharp foreground, person behind | Severe — the model gives focus to the prop and softens the face. State that the face is the focal plane. |
| Locked-off, face waist-up, even light | Best case. |
| Profile, backlit, distant | Unjudgeable — do not use these frames to verify. |

Useful lines:

```
ONE UNBROKEN CONTINUOUS TAKE, no cuts.
BOTH FACES ARE LARGE AND SHARP IN FRAME.
FOCUS: THE FACE IS THE FOCAL PLANE — the cup nearer the lens is NOT the point of focus.
IDENTITY IS CRITICAL IN THIS SHOT — @Image1 is …, @Image2 is …
```

---

## 6. Verification

**A wide frame is not verification.** Three defects passed a "verified" wide: a
soft face, a face that had become a stranger, and a whole-film character swap.

```
1. Crop the face region, scale up
2. Place beside the reference photograph
3. Judge on glasses/hardware, never on face shape — profile and low light lie
4. Confirm which person is wearing which costume
```

`templates/audit_faces.py` builds the contact sheets and a reference strip.

**Test before you commit.** Any new person, any new variant: render one shot, crop
it, get it approved, then spend on the batch. A full batch was submitted before a
de-aged face was checked; the whole first act was wasted.

---

## 7. Cast registry

Keep one authoritative file. Per person: name, height, primary reference key,
alternates, deprecated references *with the reason*, the anchor feature, the known
leak, and which films they are in.

```json
{
  "omar": {
    "name": "Omar", "height_cm": 190,
    "ref": "zac_real",
    "alt_refs": {"christmas group crop": "husband"},
    "deprecated": {"zac_young": "de-aged generation — loses the person"},
    "anchor": "bald + grey beard + build; a full head taller than her",
    "warn": "a single wide reference degrades into a generic older man — use both real photos",
    "films": ["The Word for It"]
  }
}
```

Heights across the cast are staging information: a 37 cm spread tells you who has
to stoop to meet whose eyeline. That is worth more than any adjective.

Store every reference image in one place, one folder per person, `PRIMARY` /
`alt-` / `DEPRECATED-` prefixes, plus a manifest with the hosted URLs.
