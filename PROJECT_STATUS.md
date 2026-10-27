# Project Status and Session Handoff

Last updated: 2026-10-27

Read this file at the start of the next session. It records the verified project state. Do not put API keys or other secret values in this file.

## Repository

- Local folder: `/Users/mrunalinipol/Documents/Codex/2026-10-22/hel`
- Public GitHub repository: <https://github.com/mrunalinipol/Equity-Analyst-Project>
- Branch: `main`
- Student: Mrunalini Pol
- Purdue email: `pol0@purdue.edu`
- Lab partner: Shachi Kaushik

## Secret status

- `.env` exists locally and is ignored by Git.
- `.env` contains `SEC_USER_AGENT` and a Purdue GenAI Studio API key.
- Do not print, quote, commit, or upload the API key.
- The current key was pasted into a prior chat. Revoke it and put a replacement directly in `.env` before the first model call in Lab 03.
- The public GitHub URL for `.env` returned HTTP 404 during the last verification.

## Completed work

### Lab 01

- `hello.md` exists.
- `AGENTS.md` contains the required explanation instruction.
- `check_env.py` reads `.env` and prints only the first four API-key characters followed by `...`, plus `SEC_USER_AGENT`.
- `.gitignore` excludes `.env`, `.env.*`, `.emv`, `.venv/`, Python cache files, and local application downloads.
- The repository is public and was verified without `.env`.
- The Session 1 Brightspace checkout was previously submitted.

### Week 2 pre-work

- Reading answers and the Costco filing check are in `WEEK2_PREWORK.md`.
- The paper-tool answer identifies EDGAR as the free filings reader.
- Figure 1 is identified as a workflow because code fixes its roles, hand-offs, checks, and revision path.
- The autonomy-slider answer and the unseen-company earnings-prediction limitation are recorded.
- Costco's 2026 10-K check matched net income of $9,226 million and diluted EPS of $20.76 to the XBRL facts for 2026-08-30.

### Lab 02

- `desk.py` implements the seven required data-desk steps without a hard-coded company.
- Required arguments: positional ticker.
- Optional arguments: `--peers`, `--price`, and `--step`.
- The program reads `SEC_USER_AGENT` from `.env` and sends it on SEC requests.
- The program selects the latest 10-K, 10-Q, and Item 2.02 8-K.
- The program saves the filing texts, Exhibit 99.1, facts, ratios, release evidence, peer data, and source metadata.
- Candidate XBRL tags are selected by the newest available fiscal year.
- All main-company facts use the 10-K fiscal-year end selected for revenue.
- Ratio arithmetic is calculated in code and printed.
- Both `Total revenue` and `Total revenues` release labels are supported.
- The full audit is in `LAB02_VALIDATION.md`.

Verified Costco run:

- Folder: `outputs/COST_20261027_092436`
- 10-K fiscal-year end: 2026-08-30
- Total revenue: $303.154 billion
- Operating income: $11.685 billion
- Revenue growth: 10.1437%
- Operating margin: 3.8545%
- Return on average equity: 28.4021%
- Debt to equity: 0.1721
- Free cash flow: $9.382 billion
- Diluted EPS: $20.76
- Price used: $904.70 on 2026-09-23
- P/E: 43.5790
- Latest-quarter total revenue: $95.723 billion
- Latest-quarter revenue growth: 11.1043%
- Latest-quarter diluted EPS: $6.75

Verified Walmart portability run:

- Folder: `outputs/WMT_20261027_092443`
- 10-K fiscal-year end: 2026-01-31
- Total revenue: $713.163 billion
- Operating income: $29.825 billion
- Operating margin: 4.1821%
- The run completed all seven steps with Costco, Target, and BJ's Wholesale as peers.

Validation state:

- Python version: 3.13.15.
- Three automated tests pass.
- `python -m compileall` passes.
- `git diff --check` passes.
- A public GitHub check returned HTTP 200 for the code, validation file, and Costco facts.
- A public GitHub check returned HTTP 404 for `.env`.

### Saved course material

- `papers/FRL-CanAIReplaceAnalyst.pdf` is the 9-page paper titled “Can AI match professional analysts? Evidence from a multi-agent system.”
- The uploaded PDF checksum matched the copy in Downloads.
- `library/lab02_equity_research_desk_prompt.md` contains the reconstructed Lab 02 prompt written approximately 80% toward ASD-STE100.

## Main commands

Create the environment and install packages:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run Costco:

```bash
.venv/bin/python desk.py COST --peers WMT,TGT,BJ --price 904.70
```

Run Walmart:

```bash
.venv/bin/python desk.py WMT --peers COST,TGT,BJ
```

Run one step:

```bash
.venv/bin/python desk.py COST --step 4
```

Run the tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Remaining actions

1. Revoke the exposed Purdue GenAI Studio key and put the replacement directly in `.env`.
2. Show the Lab 02 live run and saved evidence to Shachi Kaushik. Obtain her initials. An agent cannot supply partner initials.
3. Give the required two-minute explanation in person.
4. Replace the $904.70 price if the instructor assigned a different closing price.
5. Continue with Lab 03: add the four model roles, produce the five-part report, audit it by hand, and complete Checkpoint 1.

## Working rules for the next session

- Keep company-specific known answers in tests and saved evidence. Do not hard-code a company in `desk.py`.
- Keep every financial number tied to a filing line or to an XBRL tag, period, and accession.
- Use the same definition across peer comparisons.
- Do not claim that partner checks or in-person work are complete unless the student confirms them.
- Update this file before the next session ends.
