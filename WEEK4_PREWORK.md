# Week 4 pre-work

## Prepared

- `closes_reader.py` provides `official_daily_closes()` and `last_close_before()`.
- The reader uses `LSEG_CLOSES_FILE` first. If no export is configured, it uses LSEG Workspace through the isolated `.venv-lseg` environment.
- A filing at or before 4:00 PM Eastern uses the prior trading close. A filing after 4:00 PM Eastern can use that trading day's close.
- If no source has a close, the reader returns `not available`. The agent-team run continues without P/E.
- `desk.py` reads the SEC index-page `Accepted` time and saves the filing time and market-close record with the run.
- `--filed YYYY-MM-DDTHH:MM:SS` overrides the SEC time. `--price` remains accepted only for old command compatibility and is ignored.
- Only the Financial Analyst receives the official close, through the code-calculated P/E. Other roles do not receive reader output.
- `week04/edgar_examples.md` contains one current spinoff and one Form 10 filer that is not a spinoff.
- `.agents/skills/week4-prework/SKILL.md` is the required minimal repository skill.

## Install and run

Install the LSEG library in its isolated environment:

```sh
.venv/bin/python -m venv .venv-lseg
.venv-lseg/bin/python -m pip install -r requirements-lseg.txt
```

Add one data source to `.env`:

```text
LSEG_APP_KEY=your-app-key
LSEG_PYTHON=.venv-lseg/bin/python
LSEG_CLOSES_FILE=
```

If LSEG access is pending, leave `LSEG_APP_KEY` blank and set `LSEG_CLOSES_FILE` to an export file outside this repository. The reader accepts `ticker,date,close` and a single-ticker Nasdaq export with `Date,Close/Last`.

Print the last close before a filing time:

```sh
.venv/bin/python closes_reader.py --last-before TICKER 2026-11-09T16:05:00
```

Run the team with the SEC Accepted time:

```sh
.venv/bin/python crewai_flow.py TICKER --peers PEER1,PEER2
```

Run it with an override:

```sh
.venv/bin/python crewai_flow.py TICKER --peers PEER1,PEER2 --filed 2026-11-09T16:05:00
```

## Student-authored items still required

The course says that AI must not write these items.

1. Read the assigned chapters and write the two one-line responses in `week04/reading_notes.md`.
2. Write the factor list and screen window in `week04/factors.yaml`. For each factor, state its direction and chapter.
3. Open both filings in `week04/edgar_examples.md` and mark the four manual checks.
4. ~~Add an LSEG App Key to `.env`, or configure an export outside the repository.~~ Completed with an official Nasdaq export outside the repository because the signed-in LSEG account has no Workspace product entitlement.
5. ~~Run the close reader. Check one result against the exchange's official close for the same date. Record that check below.~~ Completed below.

## Close check — student record

- Ticker: UBER
- Filing accepted: 2026-11-04 06:55:39 Eastern (SEC accession 0001543151-26-000039)
- Close date: 2026-11-03
- Reader close: $66.60
- Exchange official close: $66.60
- Exchange page: <https://www.nasdaq.com/market-activity/stocks/uber/historical>
- Mark: Correct

## Skills and hooks check

- OpenAI's current skill documentation states that a skill is a folder with a `SKILL.md` file. Its name and description are the discovery metadata.
- OpenAI's plugin documentation states that installed plugin hooks are not trusted automatically. Codex skips an untrusted hook until the user reviews and trusts its current definition.
- Official pages: <https://developers.openai.com/plugins/concepts/skills> and <https://developers.openai.com/plugins/build/plugins>.
