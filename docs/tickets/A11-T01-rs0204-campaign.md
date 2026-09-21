# A11-T01 - RS0204 campaign + dual-rail bodies

**Epic:** EPIC-A11
**Status:** closed-accepted (R-0003 leftover-honest: Icc/VOH Excel grid unmapped)
**Step:** current: 4 / 4

## Problem

Founder has `RS0204 Standard_Lab_Report.xlsx` and the RevA.5 datasheet. LabAutomation-1 has no RS0204 Python (Ariff / Eugene / Lim / Soo). ATE had no RS0204 campaign.

## Acceptance

WHEN Logic campaign RS0204/TSSOP14 is Applied, THE SYSTEM SHALL list 16 tests whose `lab_sheet` matches the live workbook (VIH..tw) and SHALL NOT show OPA G11 boards.

WHEN an RS0204 test is run, THE SYSTEM SHALL use dual-rail bodies in `ate/tests/logic/rs0204.py` (VCCA <= VCCB; CH1=VCCA, CH2=VCCB). THE SYSTEM SHALL NOT import `Soo.logic_tests` or reuse RS29511 `tp`.

WHEN `python -m ate.core.check_logic_campaign` runs, THE SYSTEM SHALL pass RS0204 map coverage plus existing RS29511/RS1G08.

## Files

- `ate/config/parts/rs0204.yaml`
- `ate/tests/logic/rs0204.py`
- `#Test_Database/Logic/RS0204/TSSOP14/Version_1`
- `ate/core/check_logic_campaign.py`
