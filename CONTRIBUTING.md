# Contributing

The most valuable contribution here is **a defect and its fix**.

This repository is a failure catalogue. Its worth is not in the code — it is in the
claim that each rule was paid for. So the bar for adding a rule is evidence, and the
bar for changing one is better evidence.

## Reporting a defect

Open an issue with:

1. **The symptom**, as specifically as you can state it. "The face drifted" is not
   actionable; "the face was sharp in wides and became a different person in every
   mid-shot" is.
2. **What you tried that did not work.** Negative results are the most useful part.
   Half the rules here exist because a plausible fix failed twice first.
3. **What actually worked**, and how you confirmed it.
4. **Model and settings** — model id, resolution, aspect ratio, shot duration.

## Proposing a rule

A rule earns its place when it changes what someone does. Prefer:

- **Describe, don't negate.** If your fix is a longer `NO …` list, say so honestly —
  negatives hold until the prompt grows, then fail silently, and that is worth
  documenting too.
- **State the cost.** "This wasted a 12-shot batch" tells a reader how hard to take it.
- **Say where it stops working.** A rule with no known boundary is usually a rule
  nobody has pushed on.

## Code

- Python 3.10+, standard library only in the templates where possible.
- Comments explain *why*, and especially *what broke*. A comment that restates the code
  will be removed; a comment that records a failure will be kept forever.
- Run the linter against the example before opening a PR:

  ```bash
  cd skills/ai-film/templates
  cp ../../../examples/last-run/shots_lastrun.py .
  ./check_script.py --project lastrun --strict
  ```

- **No dollar sign followed by a digit in `SKILL.md`.** When the skill is invoked with
  arguments that sequence is substituted as a positional placeholder, and the price
  becomes a word of the user's request. Write `USD 0.45`. The references are not
  substituted, but keep them consistent.
- **Measure a claim before you write it down.** If a number in the docs came from a
  controlled test rather than a real film, say which.

## Out of scope

- Anything that helps build a likeness of a real person who did not supply the
  photograph for that purpose. See the rights section in the README.
- Prompt packs with no failure evidence behind them. There are good repos for that,
  linked in the README.
