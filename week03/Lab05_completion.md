# Lab 05 Completion Tracker

Last checked: November 8, 2026

## Completed and validated

- Partner-selected company: Uber Technologies, Inc. (`UBER`).
- Selected peers for the local evidence run: `LYFT`, `DASH`, and `ABNB`.
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
- All 29 automated tests pass. Python compilation and `git diff --check` pass.

## Fresh UBER evidence run

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
- After the personas and key are available, run UBER from the page. Use
  `LYFT,DASH,ABNB` as peers unless the student selects a different defensible
  peer set. A dated price is optional in the interface but is required for a
  P/E claim.
- The final page run must have three distinct, supported Insight lines,
  Manager status `PASS`, Verifier status `PASS`, and all marks correct.
- Shachi must run the page and independently complete the partner marks,
  corrections, name, initials, date, and signature or Git commit. No agent or
  student can fill those fields for her.
- Team formation is complete, as confirmed by the student on November 8,
  2026. The team-member names and team name are not stored in this repository.
- The student's personal reflection remains incomplete.
- Brightspace submission remains manual. No agent may submit it.
