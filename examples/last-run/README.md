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

## Running it

```bash
cd ../../skills/ai-film/templates
cp ../../../examples/last-run/shots_lastrun.py .

./check_script.py --project lastrun        # free
./generate.py    --project lastrun --dry-run
```

You will need a `refs.json` in the templates directory with two entries:

```json
{
  "driver":    ["https://…/driver-frontal.jpg",    "https://…/driver-3q.jpg"],
  "passenger": ["https://…/passenger-frontal.jpg", "https://…/passenger-3q.jpg"]
}
```

Two photographs per person, at different angles and lighting. One photograph degrades
into a *type* rather than a person. Use your own photographs with consent, or generate
original faces — do not cast a real public figure.
