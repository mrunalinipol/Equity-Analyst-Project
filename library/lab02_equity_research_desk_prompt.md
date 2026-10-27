# Lab 02 — Equity-Research Desk Prompt

Build the data component of an equity-research desk in Python. Use Section 3.1 of Francis & Zhang (2026) as the model. Do not add the model roles yet.

Use these requirements:

1. Read `SEC_USER_AGENT` from the `.env` file in this folder.
2. Send this SEC User-Agent with every SEC request.
3. Accept a ticker as a required command-line argument.
4. Accept these optional arguments:
   - `--peers`: a list of peer tickers.
   - `--price`: a price number.
   - `--step`: one step number. If specified, run only that step.
5. Do not hard-code a company name or ticker in the program.
6. Print each step when it runs.

Implement these seven steps:

1. Resolve the ticker to its CIK. Use SEC's `company_tickers.json` file.

2. Get the company's filing list from the EDGAR submissions API. Select:

   - The latest 10-K.
   - The latest 10-Q.
   - The latest 8-K whose document reports Item 2.02. Treat this filing as the earnings-release filing.

   For each selected filing, print:

   - The accession number.
   - The `Accepted` time shown on the EDGAR filing-index page.

3. Download:

   - The selected 10-K.
   - The selected 10-Q.
   - The selected Item 2.02 8-K.
   - Exhibit 99.1 from that 8-K.

   Convert each document to plain text. Save the text files in a folder whose name contains the company, run date, and run time.

4. Get the company's XBRL company facts. For the latest fiscal year, print:

   - Total revenue.
   - Operating income.
   - Net income.
   - Diluted EPS.
   - Stockholders' equity.
   - Long-term debt.
   - The current portion of long-term debt.
   - Cash from operations.
   - Additions to property and equipment.

   For each fact, also print:

   - The XBRL tag.
   - The period end.
   - The source filing.
   - The prior-year value.

   A concept can have multiple candidate tags. Select the candidate tag whose latest available year is the newest.

   Use the fiscal year selected for total revenue for every other concept. Do not combine facts from different fiscal years.

5. Implement a calculator in code. Print each result and its arithmetic. Calculate:

   - Revenue growth: current total revenue divided by prior total revenue, minus 1.
   - Operating margin: operating income divided by total revenue.
   - Return on average equity: net income divided by the average of current-year and prior-year stockholders' equity.
   - Debt to equity: long-term debt, including its current portion, divided by stockholders' equity.
   - Free cash flow: cash from operations minus additions to property and equipment.
   - P/E: the value supplied through `--price` divided by diluted EPS.

6. Read the earnings-release text. Print the lines that state:

   - The quarter's total revenue.
   - The quarter's diluted EPS.

7. For each ticker supplied through `--peers`, get the same facts. Calculate and print operating margin with the same definition used for the main company.

Save the structured facts beside the plain-text filing files.

When the work is complete, provide:

- The exact command to install all required packages.
- The exact command to run the program with a ticker, peers, and a price.
