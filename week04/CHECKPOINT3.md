# Team Ledger — Mrunalini Pol, Aditi, Shachi Kaushik

Client: an investor seeking absolute return.

## The desk

```text
start date ──> seeker.py ──> registry.json ──> ranked screen
                                               │
ticker ──> CrewAI team ──> verified_report.md  │
                           │                   │
                           └──> worksheet.py <─┘
                                  │
                                  ├──> worksheet.md ──> numeric_guard.py
                                  │
                                  └──> final_report.md ──> numeric_guard.py

investor_desk.py fixes this order and keeps all files in one run folder.
agent_team_ui.py runs investor_desk.py and shows final_report.md.
```

## The joins

The seeker is a pipeline step. The worksheet receives the agent team's saved facts and filings as files. It may quote those files and may never recompute the team's claims. The numeric guard guards the worksheet and the final report. Code fixes the order. A model chooses no step.

## We own

We own the installable investor-desk plugin. It packages the spinoff seeker, the investor worksheet, and the local numeric hook. The hook remains disabled until a student reviews and trusts its current definition.

## Roles

- Mrunalini: the agent team, the Verifier, and the joined desk.
- Aditi: the seeker registry, the worksheet skill, and the numeric guard.
- Shachi: the closes reader, partner checks, live runs, and the live-record table.

These role assignments are a prepared proposal. All three members must confirm them before submission.

## Live record so far

No qualifying live report is recorded. The saved UBER joined run is practice because its view was written after the first market reaction. It must not enter the hit-rate numerator or denominator.

| Ticker | Release | Filing time | View time | Window status |
|---|---|---|---|---|
| UBER | Q3 2026 earnings | 2026-11-04 06:55:39 Eastern | 2026-11-22, practice run | after; excluded |

The team must add the permalink for `runs/live` and one qualifying row before it submits Checkpoint 3.
