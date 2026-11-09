# Equity Research Desk

This repository contains the filing-first data desk and CrewAI Flow for FIN 67110.

## Setup

Create an isolated Python environment and install the declared packages:

```bash
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
```

The local `.env` file must contain:

```text
API_KEY=your-model-provider-key
SEC_USER_AGENT="Your Name your-email@purdue.edu"
BASE_URL="https://genai.rcac.purdue.edu/api"
MODEL="llama3.1:latest"
```

The `.env` file is ignored by Git. Never force-add it.

## Run the seven steps and CrewAI Flow

```bash
.venv/bin/python crewai_flow.py TICKER --peers PEER1,PEER2,PEER3 --price 123.45
```

Replace the ticker, peers, and price with the assigned inputs. SEC filings do
not contain a market price. The command runs the seven data steps and then
starts `EquityResearchFlow`.
CrewAI decorators fix this order in code:

`steps -> Research Analyst -> Financial Analyst -> Investment Advisor -> Strategy Manager -> Verifier`

The model cannot choose the next node. The Strategy Manager can use one
revision slot. Python selects the revision target from fixed checks, and no
specialist runs more than twice. The Verifier always runs last.

Each model role receives only `task`, `context`, and `expected_output`. Every
node input and output is saved under `flow_artifacts/` in the run folder.

Run only the seven data steps:

```bash
.venv/bin/python desk.py COST --peers WMT,TGT,BJ --price 992.13 --no-roles
```

Run one numbered step:

```bash
.venv/bin/python desk.py COST --step 4
```

Run the tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Run only the final evidence verifier:

```bash
.venv/bin/python crewai_flow.py --verify-only outputs/TICKER_YYYYMMDD_HHMMSS
```

## Lab 04 proof set

Create clean, seeded-EPS, and invented-growth copies from one saved clean run:

```bash
.venv/bin/python prepare_lab04_proofs.py outputs/COST_20261028_194706
```

The command creates three new timestamped folders under `lab04_evidence/` and
never overwrites an earlier folder. It writes the current folder paths and
expected marks to `lab04_evidence/latest_proof_index.json`.

## Lab 05 Insight checks

Each of the three analyst outputs must end with one line that begins
`Insight:`. The line must contain a number and a saved filing-line citation.
The Strategy Manager fails a part when its Insight is absent or only repeats a
figure from the first paragraph of the earnings release. Code selects one
allowed revision owner. The graph order does not change.

The Verifier checks every Insight number. It continues to skip the Investment
Advisor's thesis, but it checks the advisor's final Insight line.

The student must write the three analyst personas. Use
`LAB05_PERSONA_WORKSHEET.md`; do not replace the role files with AI-written
persona text.

## Browser page

Start the local page:

```bash
.venv/bin/python agent_team_ui.py
```

Open <http://127.0.0.1:8000>. Enter a ticker, optional peers, and an optional
price. The page streams each node name and displays `verified_report.md` when
the run finishes. Existing terminal commands continue to work.

## Replicated verifier

The final Flow node replicates the paper's evidence-checking role. Python
checks the 11 saved core claims, XBRL sources, ratio arithmetic, definitions,
and cited filing lines. The Verifier model then checks whether each line states
the number for the stated period and definition. It does not inspect the
Investment Advisor's thesis. It writes `verification.json` and
`verified_report.md`.

Verify a saved run without a model call:

```bash
.venv/bin/python verifier_agent.py outputs/COST_20261028_194706
```

Verify an edited report against the evidence from the original run:

```bash
.venv/bin/python verifier_agent.py outputs/COST_20261028_194706 --report path/to/edited-report.md
```

Apple assignment command:

```bash
.venv/bin/python desk.py AAPL --peers MSFT,GOOGL,DELL --price 338.19
```

The Apple price is the unadjusted July 29, 2026 close. The saved Apple report is
marked `fallback` because the Purdue model endpoint timed out twice. The Lab 03
instructions state that a labeled fallback report counts when the provider is down.

Each full run saves filing text, facts, calculations, release evidence, peer facts, and source metadata under `outputs/`.

This is a learning exercise, not financial advice.

AI assistance: OpenAI Codex helped build and test the filing reader. Human audit
marks remain the student's responsibility.

Any remaining errors are my own.
