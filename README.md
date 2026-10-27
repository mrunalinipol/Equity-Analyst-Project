# Equity Research Desk

This repository contains the filing-first data desk for FIN 67110 Lab 02.

## Setup

Create an isolated Python environment and install the 2 declared packages:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The local `.env` file must contain:

```text
API_KEY=your-model-provider-key
SEC_USER_AGENT="Your Name your-email@purdue.edu"
```

The `.env` file is ignored by Git. Never force-add it.

## Run the 7 steps

```bash
.venv/bin/python desk.py COST --peers WMT,TGT,BJ --price 904.70
```

The example uses Costco's September 23, 2026 close, the last close before its September 24 earnings release. Replace it with the dated price assigned by the instructor if that price differs. SEC filings do not contain a market price.

Run one numbered step:

```bash
.venv/bin/python desk.py COST --step 4
```

Run the tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Each full run saves filing text, facts, calculations, release evidence, peer facts, and source metadata under `outputs/`.

This is a learning exercise, not financial advice.

AI assistance: OpenAI Codex helped build and test the filing reader. I verified the sources myself; the judgments are mine.

Any remaining errors are my own.
