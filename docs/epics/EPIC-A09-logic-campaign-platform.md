# EPIC-A09 - Logic campaign platform (Ariff / Soo)

**PRD:** PRD-001
**Status:** implemented (R-0003 pending)
**Sliced:** 2026-09-03 (F16)
**Depends on:** A01 family rail; A02 Logic wraps; A04 timing; A08 DMM
**Appetite:** 1 wave

## Buyer-visible outcome

Logic is a manufacturable campaign like OpAmp. Team members edit specs/timing/enabled tests in YAML under `#Test_Database/Logic/...` and `ate/config/parts/`. Ariff (RS1G08) and Soo (RS29511) stay different parts on one Logic rail. Lim RS2323 stays next wave.

## Acceptance

- `#Test_Database/Logic/RS29511/...` and `Logic/RS1G08/...` campaigns exist with sheet_map + test_catalog.
- Part yaml `rs29511.yaml` / `rs1g08.yaml` drive fixture LOGIC, VCC, current_limit, timing, enabled tests.
- Run list filters by part enable list (RS29511 does not show RS1G08-only DC rows).
- Extra Ariff TestSpecs registered; no `import Ariff.*`.
- Family-aware map coverage when Logic campaign is active.
- `list_fixture_modes` returns LOGIC for Logic family (not empty, not OPA G11).
- Lim / Level / DataLogger replace out.

## Ticket

| ID | File | Status |
|----|------|--------|
| A09-T01 | [A09-T01-logic-campaign-yaml.md](../tickets/A09-T01-logic-campaign-yaml.md) | implemented (R-0003 pending) |

## Out

Lim RS2323 family; copying LabAutomation-1 owner trees into `ate/`; RS1G07 cpd/cin; Level; DataLogger replace; A01-A08 reopen.
