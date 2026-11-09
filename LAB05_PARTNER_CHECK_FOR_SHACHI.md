# Lab 05 Partner Check — Shachi

Complete this worksheet after you run the final UBER agent team from the page.
Do not complete a mark until you open the cited SEC filing or saved filing
text and check the evidence.

## Run details

- Company: Uber Technologies, Inc.
- Ticker: UBER
- Peers: AMD, YUM, DUOL, PLTR
- Run folder: `outputs/UBER_20261109_000823`
- Verified report: `outputs/UBER_20261109_000823/verified_report.md`
- Printed node order: `steps -> Research Analyst -> Financial Analyst ->
  Investment Advisor -> Strategy Manager -> Verifier`
- Automated result: Manager `PASS`; Verifier `50/50 correct`.

## Page check

- Could you start the run from the page without a terminal? Yes / No
- Did the page show each node as it ran? Yes / No
- Did the page show the verified report and its marks? Yes / No

## Core claim 1

- Claim from the report: Fiscal 2025 total revenue was `$52,017 million`.
- Filing, accession, and period: Form 10-K, accession
  `0001543151-26-000015`, year ended December 31, 2025.
- Cited XBRL fact: `us-gaap:Revenues`, USD, period ended December 31, 2025.
- Evidence to open: `saved_facts.json` records `us-gaap:Revenues` as
  `52,017,000,000` USD for the period ended December 31, 2025.
- Mark: Correct / Wrong / Unsupported
- Correction, if needed:

## Core claim 2

- Claim from the report: Q3 2026 GAAP diluted EPS was `$0.25`.
- Filing, accession, and period: Exhibit 99.1 to Form 8-K, accession
  `0001543151-26-000039`, quarter ended September 30, 2026.
- Cited saved evidence: `earnings_release_EX-99.1.txt`, lines 99-103.
- Evidence to open: lines 99-103 show the `GAAP Diluted EPS` label and the
  current-period value `$0.25`.
- Mark: Correct / Wrong / Unsupported
- Correction, if needed:

## Insight-line check

- Role: Research Analyst
- Insight line: `Insight: We are a global company and as of December 31, 2025,
  we and our subsidiaries had approximately 34,000 employees globally and
  operations in over 70 countries and more than 15,000 cities around the
  world. Our human capital strategies are developed and managed by our Chief
  People Officer, who reports to the CEO, and are overseen by the Compensation
  Committee and the Board of Directors. [10-K Line 2299]`
- Filing and cited line: Form 10-K, accession `0001543151-26-000015`, saved
  `latest_10-K.txt`, line 2299.
- Does the saved filing contain the cited evidence? Yes / No
- Does the Insight state more than the earnings release's first paragraph?
  Yes / No
- Mark: Correct / Wrong / Unsupported
- Notes:

## Partner confirmation

- Reviewer name:
- Initials:
- Date:
- Signature or Git commit:
