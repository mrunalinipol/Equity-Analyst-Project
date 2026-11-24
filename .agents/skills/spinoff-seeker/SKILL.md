---
name: spinoff-seeker
description: Find U.S. spinoffs from EDGAR, keep filing-linked facts, use the configured closes reader, and rank an evidence-bound screen.
---

# Spinoff seeker

Run the deterministic script. Do not add or estimate a fact.

```sh
.venv/bin/python week04/seeker.py --start YYYY-MM-DD
```

Use `week04/factors.yaml` without changing its factors, directions, weights, or window unless the student changes that file first. The script writes a registry, a dropped list, the exact factors used, and a dated report under `runs/seeker/`.

For each registry fact, preserve its accession, filing URL, and section. A blank fact stays blank. A Form 10 without an information statement, a fund, or a registration without a parent distribution belongs in the dropped list with its reason and filing.

The first price must be the first official close after the distribution date. End every report with `screens, not recommendations`.

Run the tests after a rule changes:

```sh
.venv/bin/python -m unittest tests.test_week04 -v
```
