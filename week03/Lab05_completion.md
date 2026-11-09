# Lab 05 Completion Tracker

Last checked: November 9, 2026

## Completed and validated

- Partner-selected company: Uber Technologies, Inc. (`UBER`).
- Selected peers for the final page run: `AMD`, `YUM`, `DUOL`, and `PLTR`.
- The graph order remains fixed: `steps -> Research Analyst -> Financial
  Analyst -> Investment Advisor -> Strategy Manager -> Verifier`.
- The Strategy Manager requires one final sourced `Insight:` line from each
  analyst and rejects a first-paragraph earnings-release restatement.
- The Manager now also rejects repeated Insight lines. A compiled report must
  preserve exactly three distinct Insight lines from the three analyst roles.
- The report and Manager artifact state `PASS` or `FAIL_UNRESOLVED`.
- The Verifier checks the number in every Insight line and still excludes only
  the Investment Advisor's thesis.
- The browser page accepts a ticker, optional peers, and an optional price. It
  streams node names and displays the verified report.
- The page returned HTTP 200 on local port 8765. Its normal start command is
  `.venv/bin/python agent_team_ui.py`; its default address is
  `http://127.0.0.1:8000`.
- `week03/Lab05_in_class_notes.md` prepares the node-order defense, the
  different-quarter Verifier answer, a filing-supported Costco gap line, and
  the persona-versus-description explanation. Personal reflection and team
  fields remain blank for the students.
- CrewAI 1.15.34 and all declared dependencies are installed in `.venv`.
- All 32 automated tests pass. Python compilation and `git diff --check` pass.

## Final COST proof run

- Final run folder: `outputs/COST_20261109_002527`.
- Inputs: COST; peers WMT, TGT, and BJ; price `$992.13`.
- Manager status: `PASS`.
- Verifier result: `verified: true`; all `22` retained marks are `correct`.
- Printed order: `steps -> Research Analyst -> Financial Analyst ->
  Investment Advisor -> Strategy Manager -> Verifier`.
- The report has three distinct `Insight:` lines, each with a correct filing
  mark. The order matches the final UBER run.

## Final UBER page run

- Final run folder: `outputs/UBER_20261109_000823`.
- Manager status: `PASS`.
- Verifier result: `verified: true`; all `50` marks are `correct`.
- Printed order: `steps -> Research Analyst -> Financial Analyst ->
  Investment Advisor -> Strategy Manager -> Verifier`.
- The report has three distinct `Insight:` lines. Each line's numbers occur on
  its cited saved 10-K line.
- The partner worksheet now names this run and its evidence. Shachi must still
  run it from the page if a review of this exact final run is required.
- On November 9, 2026, the student confirmed that the Lab 05 partner-check
  requirement is complete. The signed evidence is Shachi's public worksheet:
  <https://github.com/ShachiKaushik1742/Equity-Analyst-Project/blob/main/week03/Lab05_partner_check.md>.
  It marks two UBER claims `RIGHT` and includes Shachi's name, initials, date,
  and signature. It reviews Shachi's earlier UBER run, not this final run.

## Earlier UBER evidence run

- Valid data-only folder: `outputs/UBER_20261108_233820`.
- Latest 10-K: accession `0001543151-26-000015`, period ended December 31,
  2025.
- Latest 10-Q: accession `0001543151-26-000041`, quarter ended September 30,
  2026.
- Earnings 8-K: accession `0001543151-26-000039`, filed November 4, 2026.
- Fiscal 2025 revenue: `$52,017 million`, XBRL tag `Revenues`.
- Fiscal 2025 diluted EPS: `$4.73`, XBRL tag `EarningsPerShareDiluted`.
- Q3 2026 revenue: `$14,766 million`; Q3 2025 revenue: `$13,467 million`.
- Calculated Q3 revenue growth: `14,766 / 13,467 - 1 = 9.6458%`.
- Q3 2026 GAAP diluted EPS: `$0.25`.
- The UBER release parser now accepts a `Revenue` row, a `GAAP Diluted EPS`
  row, prior-year-first columns, and numeric footnotes in a row label.

Do not use `outputs/UBER_20261108_233532` or
`outputs/UBER_20261108_233727`. They are diagnostic runs from before both UBER
release-parser corrections.

## Required human or credential-dependent work

- The student must write the three six-part personas in their own words. The
  course prohibits AI-written personas. `LAB05_PERSONA_WORKSHEET.md` remains
  blank for this reason.
- The model-provider `API_KEY` is present in the ignored local `.env`. A
  minimal `llama3.1:latest` provider test returned `OK`. Do not commit or share
  the key.
- The final page run is complete. A dated price was not supplied, so the
  report does not make a P/E claim.
- The partner-check requirement is recorded complete by the student's
  confirmation and Shachi's signed public worksheet. The blank local worksheet
  is retained as an unused template; no agent filled Shachi's fields.
- Team formation is complete, as confirmed by the student on November 8,
  2026. The team-member names and team name are not stored in this repository.
- The student's personal reflection is complete in `week03/Lab05_personal_reflection.md`.
- Brightspace submission remains manual. No agent may submit it.

## Checkpoint 2 readiness

- The repository contains the agent team, UI, Verifier, fixed graph, seeded
  EPS-error proof, clean COST proof, and final UBER proof.
- In `lab04_evidence/COST_20261107_123023_seeded_eps/verification.json`, the
  seeded `$21.76` GAAP diluted EPS claim is `wrong`; the correction is `$20.76`
  from accession `0000909832-26-000093` and saved 10-K lines 1840-1842.
- A public commit permalink can satisfy the stated Checkpoint 2 upload field.
  The student must paste that permalink into Brightspace manually.
- The three student-drafted personas are installed in the three analyst role
  files. Each has the six required parts, numeric scoring criteria, and a final
  `Insight:` instruction. No role file names a company.
- The final-run partner package is complete in
  `LAB05_PARTNER_CHECK_FOR_SHACHI.md`, including the page checks, two core
  claim marks, one Insight-line check, and partner confirmation.
- The personal reflection is complete. Full Lab 05 repository work is ready;
  Brightspace submission remains a manual student action.
