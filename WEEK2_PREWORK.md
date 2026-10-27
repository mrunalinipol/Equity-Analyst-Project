# Week 2 Pre-work

Completed: 2026-10-27

## Reading answers

**Which paper tool does EDGAR provide for free?** EDGAR provides the filings reader: the filing list, 10-K and 10-Q documents, the earnings release in an 8-K's Exhibit 99.1, and statement facts through XBRL company facts.

**Is Figure 1 a workflow or an agent?** Figure 1 is a workflow because code fixes the roles, hand-offs, checklist, and one-revision path. The model does not choose its own process or tools.

**Where is the autonomy slider in my coding agent?** The autonomy slider is in how broadly I state the goal and which file, terminal, network, approval, and review actions I allow the agent to take without stopping.

**What could shrink the 60.35% earnings-direction edge on unseen companies and years?** The edge could shrink if training-data overlap helped the model, or if new companies and economic regimes differ from the patterns in the evaluation sample.

## Figure 1 and Figure 2

The Strategy Manager assigns JSON tasks. The JSON names the task, allowed context, and required output. The Research Analyst reads filings for the business model, market position, catalysts, and recent developments. The Financial Analyst computes statement trends, ratios, returns, leverage, cash flow, and peer comparisons. The Investment Advisor combines the first two outputs into a thesis and Buy, Hold, or Sell recommendation. The Manager checks the five required report parts, sends an incomplete draft back once, and then compiles it.

The five report parts are:

1. Overview.
2. Market Positioning and Growth Outlook.
3. Valuation Insights.
4. Future Developments and Strategic Recommendations.
5. Investment Recommendation.

## Filing definitions

- A 10-K is the annual SEC report. It contains audited annual financial statements and business disclosures.
- A 10-Q is the quarterly SEC report. It contains interim financial statements and updates.
- An 8-K reports specified material events. The earnings release is usually attached as Exhibit 99.1 to an Item 2.02 8-K.
- XBRL attaches a concept, unit, period, and filing identity to each fact. A company can change tags across years. The reader must select the tag that reaches the newest fiscal year and must keep every core fact on the 10-K fiscal-year end.

## Costco filing check

Source: Costco's 2026 10-K, fiscal year ended 2026-08-30.

- Net income attributable to Costco: **$9,226 million**.
- GAAP diluted earnings per share: **$20.76**.
- XBRL concept: `EarningsPerShareDiluted`.
- XBRL period end: `2026-08-30`.
- Filing: 10-K, accession `0000909832-26-000093`.

The filing line and the XBRL fact must match. The live Lab 02 run performs this check again before the result is accepted.

## Report-audit definitions

- Revenue growth = current total revenue / prior total revenue - 1.
- Operating margin = operating income / total revenue.
- Return on average equity = net income / average of current and prior stockholders' equity.
- Debt to equity = long-term debt, including its current portion, / stockholders' equity.
- Free cash flow = cash from operations - additions to property and equipment.

The main definition trap is revenue. Total revenue can include net sales plus membership or other revenue. A peer comparison must use the same total-revenue definition for every company.

This is a learning exercise, not financial advice.

AI assistance: OpenAI Codex helped build and test the filing reader. I verified the sources myself; the judgments are mine.

Any remaining errors are my own.
