# Add the Week 4 investor desk and Checkpoint 3 draft

## What changed

- Added the EDGAR spinoff seeker and its filing-linked registry.
- Added the investor worksheet, code-calculated owner cash flow, and explicit `not known` handling.
- Added the numeric guard, clean and seeded tests, and a reviewable local plugin hook.
- Added the one-command desk, replay, hit-rate command, and page integration.
- Added the Checkpoint 3 draft, practice three-column check, and validation record.

## Why

The desk now joins the agent team and Week 4 skills in an order fixed by code. A model does not select the order or calculate a number. Missing student inputs stop the affected calculation instead of creating a guess.

## Review requests for Aditi and Shachi

1. Confirm the team name and the proposed roles in `week04/CHECKPOINT3.md`.
2. Review `plugins/investor-desk/hooks/hooks.json` and `week04/numeric_guard.py` before anyone trusts the hook.
3. Check one Vylor registry fact against its cited filing.
4. Recompute the UBER practice owner-cash-flow line from its three printed inputs.
5. Supply the two outside-partner company names for the Lab 09 portability run.

## Validation

- 45 automated tests pass.
- All four skill folders pass the skill validator.
- Python compilation passes.
- `git diff --check` passes.
- The joined UBER practice run replays without a fetch and preserves its view time.

## Before merge

- A student completes the worksheet method, two rates, purchase size, conviction rule, and six-part persona.
- The team records one qualifying pre-reaction live report.
- The two partner-selected portability runs pass.
- The final Checkpoint 3 page has the `runs/live` permalink.

Do not merge until the team has reviewed these items. Do not include `.env`, the market-data export, API keys, or licensed book text.
