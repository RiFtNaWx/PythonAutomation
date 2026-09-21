# EPIC-A10 - Lim RS2323 + open inventory fill

**PRD:** PRD-001
**Status:** implemented (R-0003 pending)
**Sliced:** 2026-09-03 (F17)
**Depends on:** A09 Logic campaigns; A08 DMM
**Appetite:** 1 wave

## Buyer-visible outcome

Family rail **Lim** loads RS2323 current tests (I+, leakage OFF/ON, input leakage). Operator Continue for rewiring (no hanging `input()`). Logic RS1G07/RS1G14 campaigns exist. Level shows an honest empty campaign. One inventory check stays green.

## Acceptance

- Builtin family `lim` -> `ate.tests.lim`; part `rs2323.yaml`; campaign under `#Test_Database/Lim/RS2323/...`
- Four TestSpecs: iplus, leakage_off, leakage_on, input_leakage; PSU+DMM; Continue gates; no `import Lim.*`; no `input(`
- RS1G07 / RS1G14 Logic part yaml + campaigns; Level component folder exists
- `python -m ate.core.check_open_inventory` green; family_load OpAmp/Logic/Lim no cross-leak

## Ticket

| ID | File | Status |
|----|------|--------|
| A10-T01 | [A10-T01-lim-rs2323.md](../tickets/A10-T01-lim-rs2323.md) | implemented (R-0003 pending) |

## Out

RS0204; Lim configurations import; RS1G07 cpd/cin bodies; Level suite; DataLogger replace; A01-A09 reopen.
