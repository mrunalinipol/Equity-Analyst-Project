# Week 4 and Checkpoint 3 validation

Validation date: 2026-11-22.

## Completed technical work

- The closes reader and the student close check existed before this build.
- The student reading lines, factors, directions, sources, 60-day window, and two manual EDGAR classifications are present.
- `week04/seeker.py` reads EDGAR full indexes, classifies Form 10 evidence, writes a filing-linked registry, prices with `closes_reader.py`, ranks the configured factors, and ends its report with `screens, not recommendations`.
- The full one-year EDGAR run is `runs/seeker/seeker_20261122_150229`. It keeps 21 current registrants and drops 89 current non-spinoff registrants. The later verified Vylor completion filing establishes its parent, ratio, record date, distribution date, and ticker. Sagard is dropped as a fund.
- Vylor is in the 60-day window, but it is unranked because all five weighted factor inputs are unavailable. The seeker does not apply the configured tickerless UBER export to VYLR and does not invent factor values.
- `week04/worksheet.py` reads a saved team run, prints source metadata, computes owner cash flow in code, and leaves unavailable values as `not known` or `not computed`.
- `week04/numeric_guard.py` passes the clean practice worksheet and its unit test refuses a seeded result changed by one.
- `investor_desk.py` fixes the order: agent team, worksheet, worksheet guard, final assembly, final guard.
- The UBER practice run joined successfully. Replay preserved `view.json` and performed no fetch.
- The local plugin files and reviewable hook are under `plugins/investor-desk/`.
- The browser page now invokes the joined desk.
- All 45 automated tests pass. Python compilation and `git diff --check` pass.

## Claims

- The ranking claims only which configured factor hypothesis puts a name before another name for reading. The weights are not validated.
- The value range claims a long-horizon range from the stated owner-cash-flow method and student rates.
- The hit rate scores only the pre-reaction release view. It does not score the long-horizon value range.

## Required human and external work

1. A student must complete `worksheet_config.yaml`: method, low rate, mid rate, client purchase size, and conviction rule.
2. A student must write the six-part persona in `investor_persona.md`.
3. Aditi and Shachi must confirm the prepared roles and the team name.
4. A partner outside the team must supply the two Lab 09 company names. Run one command on each and replace the practice three-column table with one of those runs.
5. The team must create one qualifying pre-reaction report under `runs/live`. The UBER practice report is after the reaction and is excluded.
6. A student must review and trust the hook definition. It is prepared but not trusted automatically.
7. A student must commit and push the final verified files, add the `runs/live` permalink, and upload only `CHECKPOINT3.md` to Brightspace before 8:00 AM on 2026-11-23.
8. Add a VYLR closes-and-volume source, plus filing-linked size, coverage, and Form 4 factor inputs. Rerun the seeker until at least one name has enough inputs for a real rank.

No agent submitted, uploaded, published, or sent coursework.
