# Lab 05 Insight Request — ASD-STE100 Version

In my agent team, make each analyst output end with one line that starts with
`Insight:`. The line must state one claim and must give the filing and the
filing line that supports the claim.

Add these checks to the Strategy Manager:

1. Fail a part if its analyst output does not end with an `Insight:` line.
2. Fail a part if its `Insight:` line only repeats a figure from the first
   paragraph of the earnings release.

Send one failed part back to its owning role one time, as the current process
does. Do not let a role run more than two times.

Make the Verifier check each number in each `Insight:` line by the same rules
that it uses for other sourced numbers. Continue to exclude the Investment
Advisor's thesis, but include the Investment Advisor's final `Insight:` line.

Do not change the graph order. Do not name a company in the program code.
Keep all current command-line commands working.

Run the team with:

```bash
.venv/bin/python crewai_flow.py TICKER --peers PEER1,PEER2,PEER3 --price 123.45
```
