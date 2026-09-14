"""LAST RUN — 7 shots, 84s, English.

A worked example. Small enough to render for the price of a lunch, complete
enough to exercise every device the skill argues for.

ORIGINALITY — the premise (a bus route being discontinued) is a generic
situation, not drawn from any existing work. Characters, dialogue, camera and
the recurring object are original. Reference photographs must be either your own
with consent, or generated original faces. Do not cast a real public figure.

CAST      @Image1 = the DRIVER    @Image2 = the PASSENGER
OBJECT    a paper transfer ticket
              01  he punches it and hands it back            introduced
              04  he hands it back whole, unpunched          handed over
              06  it sits on the dash at the terminus        completed
PROMISE   "See you tomorrow."
              01  she says it to him
              04  she says it again; he does not answer      the turn
              06  he says it to an empty bus                 payoff
RHYME     the convex mirror over the windscreen, showing the whole saloon
              02  one passenger in it
              05  identical setup, nobody in it
ENDING    he says the line to nobody, and the ticket is still whole

VISUAL GRAMMAR — the film's opposition is "in service" against "out of service":

    in service   35mm, warm sodium and interior fluorescents, the frame always
                 contains at least two people-shaped things (a passenger, a
                 coat, a bag on a seat), handheld only when the bus is moving
    out of service  24mm, cold blue pre-dawn and depot worklight, locked off,
                 wide, the saloon empty and countable end to end
    between them  always a barrier: the fare box, the yellow line, the mirror.
                 In the last shot there is nothing between him and the camera.

WHY THIS EXAMPLE IS SHAPED LIKE THIS
    * 7 shots, uneven durations (8/14/10/14/16/10/12) — uniform lengths read
      like slides.
    * Two of the seven have no cast at all, so they route to text-to-video and
      cost less. Empty plates are also where the film breathes.
    * One shot is hands-only. Not showing a face is a craft tool, not just a
      constraint, and it removes an identity risk for free.
    * The dialogue is short on purpose. Budget ~4.5 characters per second plus
      0.7s between lines, and stay under ~80% of the shot.
"""

from __future__ import annotations

RESOLUTION = "1080p"
RATIO = "21:9"
BITRATE_MODE = "high"
GENERATE_AUDIO = True
LANG = "en"

LOOK = (
    "GROUNDED CONTEMPORARY DRAMA, present day, a small city at night. Live-action "
    "photography, not animation. ARRI ALEXA 65 large-format sensor, vintage anamorphic "
    "primes — oval bokeh, slight edge barrel distortion, organic film grain. "
    "LIGHTING: motivated sources only — sodium street lamps sliding past windows, the bus's "
    "own cold interior fluorescents, a lit fare box, depot worklights, pre-dawn blue. "
    "COLOUR: ACES pipeline, filmic highlight rolloff, deep retained shadow detail. Sodium "
    "amber and cold fluorescent green against wet asphalt and night blue. Never crushed, "
    "never clipped, never teal-and-orange. "
    "MOTION — AS IMPORTANT AS ANY OTHER RULE HERE: composed and unhurried, but NEVER FROZEN. "
    "EVERY shot must contain continuous visible movement in the world itself, whether or not "
    "the camera moves: street light sliding across the ceiling, rain on glass, the hand-rail "
    "straps swinging, exhaust drifting, wipers, a destination blind flickering, reflections "
    "travelling across the windows. A LOCKED-OFF CAMERA MEANS A DISCIPLINED CAMERA, NOT A "
    "STILL PHOTOGRAPH. Do NOT deliver a still image with a slow zoom on it. "
    "CAMERA: weighted and purposeful. Handheld only inside the moving bus, and only gently. "
    "No whip pans, no drone swoops, no rack-zooms. "
    "SKIN: true subsurface scattering, visible pores, end-of-shift tiredness, no retouching. "
    "PRODUCTION DESIGN: a real, worn municipal bus — scuffed grab rails, a taped seat, a "
    "printed timetable behind scratched plastic, a coin-operated fare box, a convex mirror "
    "over the windscreen. Everything used, nothing styled. "
    "NEGATIVE — avoid entirely: on-screen text, captions, subtitles, watermarks, readable "
    "signage, brand logos; plastic or waxy skin, airbrushed faces, CGI sheen, video-game "
    "render look, cartoon, anime; warped or extra fingers, uncanny symmetric faces, "
    "lens-flare spam, oversaturated grading; subjects standing dead-centre facing the lens "
    "in a flat symmetrical postcard composition with no foreground layer; crowds or extras "
    "anywhere they are not explicitly asked for."
)

# The prop gets a fixed description block, exactly like a character. "A paper
# ticket" yields a different ticket every scene and the three-beat breaks
# silently — nobody notices the break, they just stop feeling the ending.
TICKET = (
    "THE TRANSFER TICKET — the recurring object of the film, and it must look like THE SAME "
    "OBJECT in every shot: a SMALL RECTANGLE OF THIN NEWSPRINT-GREY PAPER about the size of "
    "two fingers, printed in faded blue ink with a grid of times down one edge, one corner "
    "already soft and furred from handling. When it is punched, the punch leaves a small "
    "CRESCENT-SHAPED notch in the top edge, never a round hole. "
    "It is NOT a card, NOT glossy, NOT a receipt roll, NOT a smartphone screen. "
)

PEOPLE = {
    "driver": (
        "THE DRIVER — a man in his fifties. HIS FACE MUST MATCH HIS OWN REFERENCE PHOTOGRAPHS "
        "EXACTLY, feature for feature; do not slim, sharpen, age or de-age it. The photographs "
        "win. "
        "HE WEARS THICK BLACK SQUARE-FRAMED GLASSES in every shot without exception, and a "
        "municipal transit uniform: a short-sleeved pale blue shirt with a single dark epaulette "
        "stripe on each shoulder, worn open at the collar, sleeves not rolled. "
        "PERFORMANCE: economical and courteous. He has done this route for a long time and it "
        "shows in how little he needs to look at anything. He never performs feeling."
    ),
    "passenger": (
        "THE PASSENGER — a woman in her thirties. HER FACE MUST MATCH HER OWN REFERENCE "
        "PHOTOGRAPHS EXACTLY, feature for feature; do not slim, smooth or idealise it. The "
        "photographs win. "
        "SHE ALWAYS CARRIES THE SAME BATTERED OLIVE CANVAS SHOULDER BAG with a frayed strap, "
        "in every shot without exception, and wears a dark grey work fleece over hospital "
        "scrubs. Hair tied back the same way each time. "
        "PERFORMANCE: tired, friendly, in a hurry that she is too tired to act on. She talks "
        "to him the way you talk to someone you see daily and know nothing about."
    ),
}

REF_KEY = {"driver": "driver", "passenger": "passenger"}

NO_CAST = (
    "THIS IS AN EMPTY PLATE SHOT — a locked-off plate with NO CAST AT ALL. There are no "
    "actors, no people, no figures, no silhouettes, no faces, no bodies anywhere in the frame, "
    "at any distance, including the far background and any reflection in glass or mirror. "
    "The frame contains only the vehicle, the street, the weather and the light."
)

HANDS_ONLY = (
    "THIS SHOT CONTAINS NO FACES. The only human presence is FOREARMS AND HANDS entering the "
    "frame from its edges. The frame is composed so a head cannot fit in it. No face, no head, "
    "no shoulder above the collarbone, no profile, and no reflection of a face in the glass, "
    "at any point in the shot. Ordinary working hands: short unpainted nails, dry knuckles. "
)

AUDIO_RULE = (
    "AUDIO: spoken English dialogue exactly as written, in a flat, everyday register — nobody "
    "in this film makes a speech and nobody raises their voice. Natural breath and micro-pauses; "
    "silence is allowed to sit. "
    "Plus diegetic ambience only: a diesel engine at idle and under load, air brakes, a ticket "
    "punch, coins in a fare box, rain on a metal roof, wipers, a destination blind motor, tyres "
    "on wet asphalt, an empty depot. "
    "DIALOGUE ATTRIBUTION IS CRITICAL: every line is spoken by exactly ONE person, the one "
    "named in front of it, and only that person's mouth moves on that line. NOBODY EVER SPEAKS "
    "IN UNISON. No overlapping dialogue, no chorus, no echo, no doubled voices. Lines are taken "
    "strictly in the order written, one at a time, with a clear beat between each. "
    "ABSOLUTELY NO music score, NO underscore, NO stings, NO singing, NO humming."
)

SILENT = (
    "ABSOLUTELY SILENT — no dialogue, no voices, no music, no melody, no instrument, no song, "
    "no rhythm of any kind, from any source, at any point. "
)

SHOTS: list[dict] = [
    {
        "id": "lr-00-depot",
        "duration": 8,
        "people": [],
        "action": (
            "SHOT DESIGN — LENS: 24mm, LOCKED OFF, camera low and dead centre in the aisle of a "
            "parked bus, looking down its full length toward the windscreen. "
            "FRAME: A WIDE SHOT THAT SHOWS THE ENTIRE SALOON FROM THE BACK ROW TO THE "
            "WINDSCREEN, so every seat is visible at once and can be counted. Every seat is "
            "empty. Beyond the windscreen, a depot yard before dawn. "
            "MOVEMENT IN FRAME — the bus is empty but the frame is not still: the hanging grab "
            "straps sway together in a slow shared rhythm as if the vehicle has just stopped "
            "moving; a depot worklight outside swings and throws a bar of light travelling "
            "slowly up the aisle and back; rain runs down the windscreen; the destination blind "
            "above the windscreen advances one notch with a mechanical clatter and settles. "
            "MOVE: none whatsoever. "
            "LIGHT: cold interior fluorescents, one of them flickering at a slow irregular "
            "interval, and blue-grey pre-dawn beyond the glass."
        ),
        "dialogue": SILENT + "Only rain on a metal roof and a blind motor. No voices.",
    },
    {
        "id": "lr-01-boarding",
        "duration": 14,
        "people": ["driver", "passenger"],
        "action": (
            "SHOT DESIGN — LENS: 35mm, gently handheld, close. ONE UNBROKEN CONTINUOUS TAKE. "
            "FOREGROUND: the lit fare box, close to the lens on the left and thrown out of "
            "focus — the barrier we shoot past. It stays between them all shot. "
            "FRAME: the front of a city bus at night, doors open onto wet pavement. He is in "
            "the driver's seat on the left of frame; she stands on the step at the right. "
            "BOTH FACES ARE LARGE AND SHARP. FOCUS: THE FACES ARE THE FOCAL PLANE — the fare "
            "box nearer the lens is NOT the point of focus. "
            "BLOCKING: she drops coins in the box one at a time, takes a paper transfer ticket "
            "from him, and he takes it back, punches it with a hand punch — a small metallic "
            "bite — and returns it. She folds it into her fleece pocket without looking at it. "
            "She has done this a thousand times. "
            "EYELINE: his on the punch, then briefly up at her; hers on her own hands, then out "
            "down the aisle. Neither ever looks at camera. "
            "MOVEMENT IN FRAME — rain blows in through the open door; the wipers sweep twice; "
            "headlights of a passing car travel across the inside of the bus behind them. "
            "MOVE: the handheld frame breathes and settles slightly closer as she speaks. "
            "LIGHT: the fare box glows from below; cold saloon fluorescents overhead; sodium "
            "street light through the open door."
            + TICKET
        ),
        "dialogue": (
            "Only one person speaks at a time. Four short lines, strictly in this order, with a "
            "clear pause between each. Nobody speaks in unison.\n"
            '1. PASSENGER, not really a question: "Running late again."\n'
            '2. DRIVER, punching the ticket: "You are always late."\n'
            '3. PASSENGER, already moving down the aisle: "See you tomorrow."\n'
            '4. DRIVER, to the windscreen: "See you tomorrow."\n'
            "Nobody else says anything. There is nobody else on the bus."
        ),
    },
    {
        "id": "lr-02-the-mirror",
        "duration": 10,
        "people": ["passenger"],
        "action": (
            "SHOT DESIGN — LENS: 50mm, LOCKED OFF, framed tight on the CONVEX MIRROR mounted "
            "above the windscreen, so the mirror fills most of the frame. "
            "REMEMBER THIS FRAMING PRECISELY — a later shot in this film repeats it exactly. "
            "FRAME: in the curved reflection, the whole saloon of the moving bus, distorted and "
            "bowed at the edges, every row visible at once. EXACTLY ONE PASSENGER is in it, "
            "sitting two thirds of the way back on the left, small in the reflection, looking "
            "out of the window. Her face is small but readable. Every other seat is empty. "
            "EYELINE: hers out of the side window for the whole shot — never toward the "
            "mirror, never toward the driver, never toward the lens. "
            "MOVEMENT IN FRAME — the bus is moving and everything in the reflection moves with "
            "it: street light sweeps repeatedly along the ceiling from front to back, the grab "
            "straps swing together, the whole reflected image shudders on rough road, rain "
            "streaks the windows behind her. "
            "MOVE: none whatsoever. "
            "LIGHT: cold saloon fluorescents, punctuated by sodium light strobing past."
        ),
        "dialogue": SILENT + "Only a diesel engine under load and tyres on wet road.",
    },
    {
        "id": "lr-03-the-notice",
        "duration": 14,
        "people": [],
        "hands": True,
        "action": (
            "SHOT DESIGN — LENS: 100mm macro, very shallow, LOCKED OFF, square-on to the inside "
            "of a bus window at chest height. "
            "FRAME: the frame is filled edge to edge by ONE PANE of the bus window and its "
            "rubber seal. Beyond the glass, an out-of-focus depot yard in flat grey daylight. "
            "The top edge of frame is the window's head rail and the bottom edge is the seat "
            "back; there is no room in this composition for a head or a body. "
            "BLOCKING: two hands in transit-uniform sleeves press a printed paper notice flat "
            "against the inside of the glass and smooth the air bubbles out from the centre "
            "with a thumb, then tape each corner. The paper is seen from BEHIND, so its "
            "printing is reversed and completely illegible — we never read a word of it. One "
            "hand hesitates over the last corner, then tapes it. "
            "NO READABLE TEXT ANYWHERE IN THIS SHOT. "
            "MOVEMENT IN FRAME — the paper bows and flattens under the thumb; a corner lifts "
            "and is pressed back; light shifts across the glass as cloud crosses outside; a "
            "reflection of the empty saloon slides on the pane. "
            "MOVE: none whatsoever. "
            "LIGHT: flat grey daylight through the glass, silhouetting the hands. "
            + HANDS_ONLY
        ),
        "dialogue": (
            "Two voices, both belonging to hands in frame, neither face ever seen. Only one "
            "person speaks at a time. Three short lines, strictly in this order, with a clear "
            "pause between each. They talk while working, the way two people talk about a job.\n"
            '1. FIRST VOICE: "Every window?"\n'
            '2. SECOND VOICE: "Every window. Last run is Friday."\n'
            '3. FIRST VOICE, after a beat: "Nobody reads them."\n'
            "Nobody else says anything. ABSOLUTELY NO music of any kind."
        ),
    },
    {
        "id": "lr-04-last-fare",
        "duration": 16,
        "people": ["driver", "passenger"],
        "action": (
            "SHOT DESIGN — LENS: 35mm, gently handheld, close. ONE UNBROKEN CONTINUOUS TAKE. "
            "THIS IS THE SAME SETUP AS THE BOARDING SHOT EARLIER IN THE FILM — same lens, same "
            "position, same lit fare box in the near foreground, same two positions in frame. "
            "The composition is the same; everything else has changed. "
            "FRAME: the front of the bus at night, doors open. He is in the driver's seat on the "
            "left; she stands on the step at the right. Taped to the window behind her head is "
            "the printed notice, seen from behind and illegible. "
            "BOTH FACES ARE LARGE AND SHARP. FOCUS: THE FACES ARE THE FOCAL PLANE. "
            "BLOCKING: she drops the coins in. He takes a paper transfer ticket, and then does "
            "NOT punch it — he holds the punch, does not close it, and hands the ticket back "
            "WHOLE, with no notch in its top edge. She takes it, and for the first time in the "
            "film she looks at it before putting it away. Then she looks at him. He does not "
            "look up. "
            "EYELINE: hers down at the unpunched ticket, then at him and held there; his down at "
            "the wheel throughout. He does not look at her once. Neither looks at camera. "
            "MOVEMENT IN FRAME — rain blows in through the open door; the wipers sweep; a "
            "passing car's headlights travel across the inside of the bus; the destination blind "
            "above the windscreen is showing NOT IN SERVICE and it flickers. "
            "MOVE: the handheld frame drifts fractionally and then goes still when he does not "
            "answer, and stays still, held past comfortable. "
            "LIGHT: identical to the boarding shot — fare box from below, cold fluorescents "
            "overhead, sodium through the door."
            + TICKET
        ),
        "dialogue": (
            "Only one person speaks at a time. Four short lines, strictly in this order, with a "
            "clear pause between each, and a very long silence where marked. Nobody speaks in "
            "unison.\n"
            '1. PASSENGER, seeing the ticket is unpunched: "You forgot."\n'
            '2. DRIVER, still not looking up: "No."\n'
            "(A long silence. She understands. Neither of them fills it.)\n"
            '3. PASSENGER, quietly, the same way she says it every night: "See you tomorrow."\n'
            "(He does not answer. He does not answer at all. She goes down the aisle.)\n"
            "Nobody else says anything. There is nobody else on the bus."
        ),
    },
    {
        "id": "lr-05-the-mirror-again",
        "duration": 10,
        "people": [],
        "action": (
            "SHOT DESIGN — LENS: 50mm, LOCKED OFF, framed tight on the CONVEX MIRROR above the "
            "windscreen, so the mirror fills most of the frame. "
            "FRAME: the convex mirror above the windscreen, filling most of the frame, with the "
            "bowed reflection of the whole saloon in it. "
            "THIS IS A PRECISE REPEAT OF AN EARLIER SHOT IN THIS FILM AND MUST MATCH IT EXACTLY "
            "— same lens, same distance, same framing of the same mirror, the same bowed "
            "reflection of the same saloon, the same rows visible. THE COMPOSITION IS "
            "IDENTICAL. The only difference is that THERE IS NOBODY IN THE REFLECTION. Every "
            "seat is empty, including the seat two thirds of the way back on the left. "
            "ABSOLUTELY NO people, figures or silhouettes anywhere in the mirror or the frame. "
            "MOVEMENT IN FRAME — the bus is still moving and everything in the reflection moves: "
            "street light sweeps along the ceiling front to back exactly as before, the grab "
            "straps swing together, the image shudders on rough road, rain streaks the windows. "
            "Nothing about the movement has changed either. "
            "HOLD THE SHOT past comfortable. "
            "MOVE: none whatsoever. "
            "LIGHT: identical — cold fluorescents, sodium strobing past."
        ),
        "dialogue": SILENT + "Only a diesel engine under load and tyres on wet road.",
    },
    {
        "id": "lr-06-terminus",
        "duration": 12,
        "people": ["driver"],
        "action": (
            "SHOT DESIGN — LENS: 40mm, LOCKED OFF, from the aisle just behind the driver's "
            "shoulder, slightly wide. "
            "FOREGROUND: nothing. FOR THE FIRST TIME IN THIS FILM THERE IS NOTHING BETWEEN THE "
            "CAMERA AND HIM — no fare box, no mirror, no glass, no yellow line. "
            "FRAME: the terminus before dawn. The bus is stopped, engine off, doors shut. He "
            "sits in the driver's seat with his hands off the wheel. On the dashboard shelf in "
            "front of him, alone, lies THE TRANSFER TICKET — the same paper rectangle, still "
            "WHOLE, with no notch in its top edge. HIS FACE IS SHARP AND CLEARLY READABLE. "
            "BLOCKING, in this exact order and no more than this: he looks at the ticket. He "
            "does not pick it up. He takes his glasses off, folds them, and puts them on the "
            "shelf beside it. Then he sits. "
            "EYELINE: on the ticket, then out through the windscreen at nothing. Never at camera. "
            "MOVEMENT IN FRAME — the engine is off but the world is not still: the sky beyond "
            "the windscreen is visibly lightening from black to grey across the shot; rain has "
            "stopped and water still runs down the glass in slow beads; the hanging grab straps "
            "behind him settle one last time and hang still; his breath is faintly visible. "
            "MOVE: an extremely slow push-in that ends on him and the ticket in the same frame — "
            "the move brings the object and the man together, and that is its reason. "
            "LIGHT: no interior lights, only pre-dawn blue-grey through the windscreen."
            + TICKET
        ),
        "dialogue": (
            "ONE speaker, ONE line in the entire shot.\n"
            "(A long time with no voice at all. Only water on glass and a cooling engine ticking.)\n"
            '1. DRIVER, to an empty bus, quietly, exactly the way he says it every night: '
            '"See you tomorrow."\n'
            "(Nobody answers. There is nobody else on the bus and nobody outside it.)\n"
            "No second voice, no voice-over, no reply. ABSOLUTELY NO music of any kind."
        ),
    },
]

TOTAL_S = sum(s["duration"] for s in SHOTS)  # 84

# What a stranger needs, and the line that says it. check_script.py errors on any
# fact nobody speaks. The first draft of this film never said the route was ending:
# the notice is deliberately unreadable, so nothing did.
CAUSAL_CHAIN = [
    ("they see each other every night",   "See you tomorrow."),
    ("the route is being discontinued",   "Last run is Friday."),
    ("he lets her keep the ticket whole", "You forgot."),
]

# ~95% hard cuts. Dip to black only for a time ellipsis or an act boundary.
# Note the deliberate hard cut into the notice shot: the route being cancelled
# should arrive without warning, and a transition there would telegraph it.
FADES: dict[str, tuple[float, float]] = {
    "lr-00-depot":            (1.0, 0.0),
    "lr-01-boarding":         (0.0, 0.0),
    # 01 -> 02 hard cut: same night, moments later.
    "lr-02-the-mirror":       (0.0, 0.7),
    "lr-03-the-notice":       (0.7, 0.8),   # isolated at both ends: this is the turn
    "lr-04-last-fare":        (0.8, 0.0),
    # 04 -> 05 hard cut: the empty mirror must land immediately after she leaves.
    "lr-05-the-mirror-again": (0.0, 1.2),
    "lr-06-terminus":         (1.2, 2.0),
}

# Burned-in cards are opt-in. This film uses none.
NAME_CARDS: list[tuple[str, float, float, float, float, int]] = []

MUSIC_PROMPT = (
    "Sparse, gentle instrumental score for a quiet contemporary drama about the end of a "
    "routine. A solo upright piano with soft felt hammers, recorded close in a real room so the "
    "felt, the pedal and the room tone are audible. Slow single notes with long silences "
    "between them; the piece is mostly space. One cello enters low and warm in the middle third, "
    "holds long legato notes underneath, and leaves. Ends on a single held piano note with the "
    "sustain pedal down, decaying into room noise. "
    "Warm, tender, resigned. Never cold, never agitated, never tense, never suspenseful. "
    "No percussion, no drums, no brass, no choir, no voices, no synth, no arpeggios, no "
    "electronic elements, no strings section, no orchestra, no crescendo, no dissonance."
)


def _cast(shot: dict, refs: dict) -> str:
    people = shot.get("people", [])
    if not people:
        return HANDS_ONLY if shot.get("hands") else NO_CAST
    lines, n = [], 1
    for who in people:
        value = refs[REF_KEY[who]]
        count = len(value) if isinstance(value, list) else 1
        tags = ", ".join(f"@Image{n + i}" for i in range(count))
        verb = "are ALL THE SAME PERSON:" if count > 1 else "is"
        lines.append(f"{tags} {verb} {PEOPLE[who]}")
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
    return "\n\n".join([shot["action"], _cast(shot, refs), LOOK, AUDIO_RULE, shot["dialogue"]])
