# Lab 03 Notes

## Gap check

The Financial Analyst is the role most likely to get a number wrong. A model can recalculate a supplied ratio, produce a plausible rounded answer, and omit the source definition. The first trial did this: it changed verified revenue growth from 10.1437% to 9.99% and quarter revenue growth from 11.1043% to 10.11%.

The harness now gives the role a calculator-built block and refuses a draft that changes or omits a required value. It permits one revision. If that revision still fails, the harness uses the calculator-built block instead of the rejected model text.

## Human sign-off

Anthropic's financial-services repository says its agents draft analyst work for review by a qualified professional. The agents do not make investment recommendations, execute transactions, bind risk, post to a ledger, or approve onboarding. Every output is staged for human sign-off.

Those agents add domain skills, data connectors, workflow-specific controls, and an explicit professional-review boundary. This desk had EDGAR data and a calculator, but it initially lacked a strong refusal check between plausible model prose and a report ready for review.

Source: <https://github.com/anthropics/financial-services>

## Costco run

- Report: `outputs/COST_20261028_194706/report.md`
- Tuesday close supplied to the desk: $992.13 on 2026-10-27.
- P/E: 47.7905x, calculated as `992.13 / 20.76`.
- The five required parts are present.
- The eleven core claims are present with filing accessions, XBRL tags or Exhibit 99.1 lines, periods, definitions, and arithmetic.
- The human audit template is `audits/COST_20261028_human_audit.md`.

## Work that requires the student or partner

1. Mrunalini must fill the Costco audit marks by hand. AI must not supply the marks.
2. Shachi Kaushik must choose a U.S. company that reported this month.
3. Run the same desk on that ticker with suitable peers and a dated close.
4. Shachi must check two core claims in that report and write both marks at the top of its file.
5. Mrunalini must audit all eleven partner-company claims before Session 4.
