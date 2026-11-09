# Lab 05 In-Class Notes

These notes prepare the required discussion. The student and partner must still
perform and confirm the live actions themselves.

## Open and defend

Fixed node order:

`steps -> Research Analyst -> Financial Analyst -> Investment Advisor -> Strategy Manager -> Verifier`

If a number appears in the earnings release but belongs to a different
quarter, the Verifier must not accept it for the stated quarter. It checks the
period and definition, not only whether the number occurs somewhere in the
release. It should mark the claim `wrong` when the correct period-specific
value is available and give the correction. It should mark the claim
`unsupported` when the saved evidence cannot establish the stated value for
the stated period.

Costco gap-check line:

`Costco opened 28 new warehouses in fiscal 2026, including three relocations, for 25 net new warehouses. [10-K Line 1328]`

The 10-K supports this claim. The earnings release's first announcement
paragraph, saved at Exhibit 99.1 lines 9-10, states quarterly and annual net
sales but does not state the warehouse-opening claim.

## D — common question

Yes, each role can express a stable point of view through a student-written
persona, while the model fills that structure with company-specific evidence
on each run. The role must make at least one filing-supported claim that is
not only a restatement of the release's first paragraph. The fixed Manager and
Verifier checks make the process portable to a company selected by a partner.

## Persona, not prompt

An instruction file fixes the role's identity, reading method, inputs, scored
criteria, evidence that changes its view, and required output. The model then
applies those fixed rules to each company's filings.

The Verifier can check whether a number, filing line, period, definition, and
calculation match the saved evidence. A reader must judge whether the selected
criteria are useful, whether the weights express a sensible investor point of
view, and whether the final Insight is decision-relevant.

A persona that scores adds an explicit decision rule. It makes the role rank
evidence, show trade-offs, and produce comparable results across companies. A
role that only describes can summarize many facts without showing which facts
matter or how they change the conclusion.

## Reflection prompts requiring the student's judgment

1. Insight line trusted least:
2. Exact reason it is less reliable:
3. Team member whose agent team will be the starting point:
4. What that agent team still lacks:

## Team formation requiring the students

- Status: Complete — confirmed by the student on November 8, 2026.
- The team-member names and team name are not stored in this repository.
