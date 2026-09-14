# Last Run

**7 shots · 84 seconds · English · ~$38 to render**

A night bus driver, a passenger who rides every night, and a paper transfer ticket.
On the last run of a discontinued route, he hands the ticket back without punching it.

This example exists to be read, not admired. It is deliberately small enough to render
cheaply and complete enough to exercise everything the skill argues for.

## What it demonstrates

| Device | Where |
|---|---|
| **The object** — a paper transfer ticket | punched (01) → handed back whole (04) → alone on the dash (06) |
| **The promise** — *"See you tomorrow."* | she says it (01) → she says it and he does not answer (04) → he says it to an empty bus (06) |
| **The rhyming shot** — the convex mirror | one passenger in the reflection (02) → identical setup, nobody in it (05) |
| **Empty plates** | 00 and 05 have no cast, so they route to text-to-video and cost less |
| **Hands without faces** | 03 is forearms and hands only — no identity risk, and stronger than showing who |
| **The barrier ladder** | the fare box, the yellow line, the mirror — and nothing at all in the final shot |
| **Uneven durations** | 8 / 14 / 10 / 14 / 16 / 10 / 12 — uniform lengths read like slides |
| **Transitions as narrative** | 3 of 6 boundaries are hard cuts; the route cancellation arrives without warning |
| **A causal chain, linted** | `CAUSAL_CHAIN` pairs each fact with the line that says it. The first draft never said the route was ending — the notice is deliberately unreadable, so nothing did. The stranger audit caught it; 03 now says *"Last run is Friday."* |

## Running it

```bash
cd ../../skills/ai-film/templates
cp ../../../examples/last-run/shots_lastrun.py .

./check_script.py --project lastrun          # free
./check_script.py --project lastrun --script # read only the dialogue, as a stranger
./generate.py    --project lastrun --dry-run
```

You will need a `refs.json` in the templates directory with two entries:

```json
{
  "driver":    ["https://…/driver-frontal.jpg",    "https://…/driver-3q.jpg"],
  "passenger": ["https://…/passenger-frontal.jpg", "https://…/passenger-3q.jpg"]
}
```

Name photos `refs/<key>-1.jpg`, `refs/<key>-2.jpg` and print that map with
`./pika_client.py upload refs/*.jpg > refs.json`.
Set `PIKA_API_KEY` first.

Two photographs per person, at different angles and lighting, is best. A single *wide*
photograph degrades into a *type* rather than a person; a single clean frontal one can
hold if the face stays large and front-on. Use your own photographs with consent, or generate
original faces — do not cast a real public figure.
