# Lab 05 User-Interface Request — ASD-STE100 Version

Add a user interface to my agent team.

Make one page where a person can:

- enter a ticker;
- enter optional peer tickers;
- enter an optional price;
- start the agent team;
- see each node name when the node starts; and
- read the saved verified report and its marks when the run ends.

The person must not need to open a terminal to run an analysis after the page
has started. Keep all current command-line commands working. Do not change the
graph order. Do not add an option that skips the Verifier. Do not name a
company in the program code.

Start the page with:

```bash
.venv/bin/python agent_team_ui.py
```

Then open <http://127.0.0.1:8000>.
