---
name: investor-worksheet
description: Build an investor worksheet from a saved filing-first run, print owner-cash-flow and value arithmetic, and refuse unsupported numbers.
---

# Investor worksheet

Read `week04/worksheet_config.yaml` and `week04/investor_persona.md` first. If either contains `STUDENT TODO`, do not invent the missing content. Run the worksheet and let the affected result be `not computed`.

```sh
.venv/bin/python week04/worksheet.py RUN_FOLDER --registry SEEKER_RUN/registry.json
```

The model can write only the qualitative judgment. Code must fill facts, calculate owner cash flow and value cases, compare the price, add liquidity, and record the view. No model calculates a number.

Run the numeric guard on the saved output:

```sh
.venv/bin/python week04/numeric_guard.py RUN_FOLDER/worksheet.md --run RUN_FOLDER
```

On a failure, report the exact refused line and continue the task. Do not say that the output is done.
