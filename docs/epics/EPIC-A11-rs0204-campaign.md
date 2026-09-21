# EPIC-A11 - RS0204 campaign + workbook honesty

**PRD:** PRD-001
**Status:** implemented (R-0003 pending)
**Sliced:** 2026-09-03 (F18)
**Depends on:** A09 Logic campaigns
**Appetite:** 1 wave

## Buyer-visible outcome

Logic rail Apply **RS0204** (TSSOP14) uses the real `RS0204 Standard_Lab_Report.xlsx`. All 16 test sheets are listed. Bodies are dual-rail in `ate/tests/logic/rs0204.py` (PSU CH1=VCCA, CH2=VCCB). Do not wrap RS29511/Soo.

## Acceptance

- Campaign `#Test_Database/Logic/RS0204/TSSOP14/Version_1` with live workbook + sheet_map
- Part yaml `rs0204.yaml`; 16 TestSpecs whose `lab_sheet` matches the xlsx
- `python -m ate.core.check_logic_campaign` includes RS0204
- Run of `vih` requires instruments (not a missing-recipe stub); no `Soo.logic_tests`
- No overwrite of Soo `tp` id (`tp_rs0204` for B->A)

## Ticket

| ID | File | Status |
|----|------|--------|
| A11-T01 | [A11-T01-rs0204-campaign.md](../tickets/A11-T01-rs0204-campaign.md) | implemented (R-0003 pending) |

## Out

QFN/UQFN extra campaigns; DataLogger replace; A01-A10 reopen.
