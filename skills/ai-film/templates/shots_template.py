"""<TITLE> — <N> shots, <TOTAL>s.

Copy this to `shots_<project>.py` and replace everything in <angle brackets>.
Read `references/story.md` before writing scenes and `references/prompting.md`
before writing shot designs.

STATE THE ORIGINALITY CONTRACT HERE. For example:

    Genre premise and setting are public domain. Characters, plot, dialogue,
    camera and the recurring object are original and are not drawn from any
    existing work. Reference photographs are <supplied with consent | generated
    original faces>; no real public figure's likeness is used.

CAST      @Image1 = <NAME_A>   @Image2 = <NAME_B>
OBJECT    <the small physical thing that appears exactly 3 times>
PROMISE   <the plain spoken line: established -> handed back -> completed>
RHYME     <the two shots with an identical setup, separated by the turn>
ENDING    <one line>

VISUAL GRAMMAR — assign the film's central opposition two photographic
languages and obey it in every shot:

    <side A>   <lens / composition / light>
    <side B>   <lens / composition / light>
    together   <what always stands between them, until it does not>

CONTRACT — what generate.py and finish.py read from this module:

    SHOTS              required. list[dict]; see the shot schema below
    build_prompt()     required. (shot, refs) -> str
    build_image_urls() required. (shot, refs) -> list[str]  ([] routes to t2v)
    REF_KEY            required by audit_faces.py. character -> refs.json key
    RESOLUTION / RATIO / BITRATE_MODE / GENERATE_AUDIO   optional, defaults shown
    LANG               optional. "zh" (default) or "en" — picks the subtitle font
    FADES              optional. shot id -> (fade_in_s, fade_out_s)
    NAME_CARDS         optional. burned-in cards; opt-in only
    MUSIC_PROMPT       optional. overrides the default score brief

Shot schema:

    id          str    unique, and namespaced if you keep several projects
                       side by side (two films both having "00-title" once
                       applied one film's transitions to the other)
    duration    int    seconds, 4-30
    people      list   character keys; [] means an empty plate -> text-to-video
    action      str    the shot design; see the six elements in prompting.md
    dialogue    str    the lines, with delivery direction
"""

from __future__ import annotations

RESOLUTION = "1080p"
RATIO = "21:9"
BITRATE_MODE = "high"
GENERATE_AUDIO = True
LANG = "zh"

# ── Photographic texture. Global. Says nothing about composition — that is each
#    shot's job.
LOOK = (
    "HOLLYWOOD TENTPOLE <GENRE>, <ERA>. Live-action photography, not animation. "
    "ARRI ALEXA 65 large-format sensor, vintage anamorphic primes — oval bokeh, slight edge "
    "barrel distortion, organic 65mm film grain, subtle gate weave. "
    "LIGHTING: motivated sources only — <list them>. 4:1 key-to-fill, hard rim separation, "
    "volumetric haze, catchlights in the eyes. "
    "COLOUR: ACES pipeline, filmic highlight rolloff, deep retained shadow detail. "
    "<palette per side of the opposition>. Never crushed, never clipped. "
    # Composed stillness is not a frozen frame. Without this block you get a
    # photograph with a slow zoom on it, and you pay full price for it.
    "MOTION — AS IMPORTANT AS ANY OTHER RULE HERE: this film is composed and unhurried but "
    "NEVER FROZEN. EVERY SHOT must contain continuous visible movement in the world itself, "
    "whether or not the camera moves: moving air, drifting haze and dust in light, light "
    "changing across a wall, weather crossing, water, cloth lifting, steam, running machinery, "
    "screens changing, distant traffic, reflections travelling across glass. "
    "A LOCKED-OFF CAMERA MEANS A DISCIPLINED CAMERA, NOT A STILL PHOTOGRAPH. Do NOT deliver a "
    "still image with a slow zoom. Do NOT give a shot where the only thing moving is a mouth. "
    "CAMERA: heavy dolly and technocrane — slow, weighted, purposeful. No handheld jitter, "
    "no whip pans, no drone swoops. <state the one exception if the film has one>. "
    "SKIN: true subsurface scattering, visible pores, fine facial hair, natural oil sheen. "
    "PRODUCTION DESIGN: <period/genre specifics>, real materials with weight and wear. "
    "NEGATIVE — avoid entirely: on-screen text, captions, subtitles, watermarks, chat windows, "
    "messaging interfaces, holographic UI, readable displays of any kind; plastic or waxy skin, "
    "airbrushed faces, CGI sheen, video-game render look, cartoon, anime, uncanny symmetric "
    "faces, warped or extra fingers, lens-flare spam, oversaturated teal-orange grading; "
    "subjects standing dead-centre facing the lens; flat symmetrical postcard compositions "
    "with no foreground layer."
)

# ── Identity. Hardware anchors carry this; adjectives do not.
#    Give every character at least one hard object that exists in their photo.
#    NEVER write a physical attribute that contradicts the reference photograph:
#    the model follows the adjective, not the @ImageN tag, and will swap two
#    characters for an entire film.
PEOPLE = {
    "<a>": (
        "<NAME_A> — <age bracket>, <ethnicity>. HER/HIS FACE MUST MATCH THE REFERENCE "
        "PHOTOGRAPHS EXACTLY, feature for feature. Do not slim, sharpen, age, de-age or "
        "idealise the face. The photographs win. "
        "<HARD OBJECT — e.g. THIN SILVER SQUARE RECTANGULAR SPECTACLES worn in every shot>. "
        "<hair, stated absolutely>. "
        "WARDROBE: <specific garments with one distinguishing detail>. "
        "PERFORMANCE: <how they behave, not how they look>."
    ),
    "<b>": (
        "<NAME_B> — … same shape as above, with a DIFFERENT hard object …"
    ),
}

REF_KEY = {"<a>": "<refs.json key>", "<b>": "<refs.json key>"}

# ── A recurring prop needs a fixed description block, exactly like a character.
#    "A small notebook" yields a different notebook every scene and the object's
#    three-beat breaks silently — nobody notices the break, they just stop
#    feeling the ending.
PROP = (
    "THE <PROP> — the recurring object of the film, and it must look IDENTICAL in every shot "
    "it appears in: <size, material, colour, one distinctive flaw>. "
    "It is NOT <the three things the model will substitute>. "
    "It gets more worn as the film goes on but it is always the same object. "
)

# ── For shots with no cast. Do NOT add "no people" to a prompt that also carries
#    PEOPLE — they fight and casting wins. Swap the block instead.
NO_CAST = (
    "THIS IS AN EMPTY PLATE SHOT — a locked-off plate with NO CAST AT ALL. There are no "
    "actors, no people, no figures, no silhouettes, no faces, no bodies anywhere in the frame, "
    "at any distance, including the far background and any reflection in glass. The frame "
    "contains only environment, structure, weather, objects and light."
)

# ── Hands without faces. Neither block above fits: casting grows a face, and
#    "no people" contradicts the hands.
HANDS_ONLY = (
    "THIS SHOT CONTAINS NO FACES. The only human presence is FOREARMS AND HANDS entering the "
    "frame from its edges. The frame is composed so a head cannot fit in it. No face, no head, "
    "no shoulder above the collarbone, no profile, no reflection of a face in any surface, at "
    "any point in the shot. "
)

# ── The music ban is mandatory. Without it the model composes a score, the score
#    trips a copyright fingerprint, and the job is rejected AFTER the video has
#    finished rendering — you pay and get nothing.
AUDIO_RULE = (
    "AUDIO: spoken <LANGUAGE> dialogue exactly as written, performed with restrained, sincere, "
    "deeply felt emotion — quiet intensity, never shouting or melodramatic. Natural breath and "
    "micro-pauses. Plus diegetic ambience only: <specific sounds>. "
    "DIALOGUE ATTRIBUTION IS CRITICAL: every line is spoken by exactly ONE person, the one "
    "named in front of it, and only that person's mouth moves on that line. "
    "NOBODY EVER SPEAKS IN UNISON. No two characters say the same words at the same time. "
    "No overlapping dialogue, no chorus, no echo, no doubled voices. Lines are taken strictly "
    "in the order written, one at a time, with a clear beat between each. "
    "ABSOLUTELY NO music score, NO orchestral score, NO underscore, NO stings, NO singing."
)

# ── Title and end cards must declare silence explicitly. With nothing to say the
#    model invents ambience or music and trips the same copyright filter.
SILENT = (
    "ABSOLUTELY SILENT — no dialogue, no voices, no music, no melody, no instrument, no song, "
    "no rhythm of any kind, from any source, at any point. "
)

# ── Scenes. Uneven durations; uniform lengths read like slides.
#    Four acts, roughly 25% / 27% / 30% / 18%.
#    Keep each shot to at most THREE simultaneous demands: ask for five and the
#    model does the cheapest one.
#    Budget dialogue at ~4.5 characters/second plus 0.7s between lines, and keep
#    speech under ~80% of the shot. Past that the model rushes or drops lines.
SHOTS: list[dict] = [
    {
        "id": "<xx>-00-title",
        "duration": 8,
        "people": [],
        "action": (
            "SHOT DESIGN — LENS: <focal length + why>. "
            "MOVE: <the move AND its reason>. "
            "FRAME: <what is in it and where>. "
            "MOVEMENT IN FRAME: <what moves even though the camera does not>. "
            "LIGHT: <direction and quality>."
        ),
        "dialogue": SILENT + "Only a faint room tone.",
    },
    {
        "id": "<xx>-01-<slug>",
        "duration": 14,
        "people": ["<a>", "<b>"],
        "action": (
            "SHOT DESIGN — LENS: <focal length + why>. "
            "FOREGROUND: <something close and soft we shoot past — this creates depth>. "
            "FRAME: <who sits on which third; what the negative space means>. "
            "BLOCKING: <what they DO; people in films are never just standing>. "
            "EYELINE: <where each looks — and 'never at camera'>. "
            "MOVE: <the move AND its reason: 'a push-in that ends when her hand stops'>. "
            "MOVEMENT IN FRAME: <weather, light, machinery, cloth>. "
            "LIGHT: <direction and quality>. "
            "SETTING: <place, time of day, weather>."
        ),
        "dialogue": (
            "Only one person speaks at a time. <N> short lines, strictly in this order, with a "
            "clear pause between each. Nobody speaks in unison.\n"
            "1. <NAME_A>, <delivery direction>: 「<line>」\n"
            "2. <NAME_B>, <delivery direction>: 「<line>」\n"
            "Nobody else says anything."
        ),
    },
    # ... 8-13 shots total.
]

TOTAL_S = sum(s["duration"] for s in SHOTS)

# ── Transitions. ~95% hard cuts. Dip to black only for a time ellipsis or an act
#    boundary. Fades are applied inside each clip, so the runtime stays exact.
FADES: dict[str, tuple[float, float]] = {
    # "<xx>-00-title": (1.0, 0.6),
}

# ── Burned-in cards are opt-in. Leave empty unless the film needs them.
#    (text, start_s, duration_s, x_fraction, y_fraction, font_px)
NAME_CARDS: list[tuple[str, float, float, float, float, int]] = []

# ── Score brief. Instrument family matters more than mood.
MUSIC_PROMPT = ""


def _cast(shot: dict, refs: dict) -> str:
    """The conditional here is load-bearing — see NO_CAST above."""
    people = shot.get("people", [])
    if not people:
        return HANDS_ONLY if shot.get("hands") else NO_CAST
    override = shot.get("desc_override", {})
    lines, n = [], 1
    for who in people:
        value = refs[REF_KEY[who]]
        count = len(value) if isinstance(value, list) else 1
        tags = ", ".join(f"@Image{n + i}" for i in range(count))
        verb = "are ALL THE SAME PERSON:" if count > 1 else "is"
        lines.append(f"{tags} {verb} {override.get(who, PEOPLE[who])}")
        n += count
    return (
        "CASTING — faces held rigidly consistent with their reference photographs (bone "
        "structure, eye shape, nose, jawline, hairline). Assign each person strictly by their "
        "own tagged photograph and never swap them:\n" + "\n".join(lines)
    )


def build_image_urls(shot: dict, refs: dict) -> list[str]:
    urls: list[str] = []
    for who in shot.get("people", []):
        value = refs[REF_KEY[who]]
        urls += value if isinstance(value, list) else [value]
    return urls


def build_prompt(shot: dict, refs: dict) -> str:
    # Load-bearing constraints belong early, in the action text. A global rule
    # buried after 800 words of look description loses weight as the prompt grows.
    return "\n\n".join([shot["action"], _cast(shot, refs), LOOK, AUDIO_RULE, shot["dialogue"]])
