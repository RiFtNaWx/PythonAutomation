# EPIC-A12 - Ariff latest Logic into ATE

**PRD:** [PRD-001-ate-multi-product-platform](../prd/PRD-001-ate-multi-product-platform.md)
**Repo:** PythonAutomation
**Status:** implemented (R-0003 pending)
**Sliced:** 2026-09-04 (F21)
**Tier:** family wrap completeness
**Depends on:** EPIC-A09 Logic campaign; A02 wraps
**Blocks:** none hard
**Appetite:** 1 wave
**GitHub Issues:** do not open unless founder opts in

---

## Buyer-visible outcome

Operator on Logic / RS1G08 sees the full Ariff DC + VOH/VOL set (including new `vih_vil`, `voh_load`, `vol_load`, `supply_current_sweep`). Unused rows stay unchecked. Soo RS29511 still shows only Soo tests. No `import Ariff.*`.

---

## Acceptance

> WHEN Logic family loads, THE SYSTEM SHALL register thickened Ariff DC bodies (8-combo off_current, pin-force ioff_leakage, VCC-swept leakage, supply_current_sweep) plus `vih_vil` / `voh_load` / `vol_load` without importing Ariff.*. WHEN part_key is rs1g08/rs1g32/rs1gt32d, THE SYSTEM SHALL list those ids in enabled_tests. WHEN part_key is rs29511, THE SYSTEM SHALL NOT list Ariff-only ids. WHEN `python -m ate.core.check_logic_campaign` runs, THE SYSTEM SHALL pass with the new ids on rs1g08 and Soo catalog isolation.

**Ticket-level:**

- `ate/tests/logic/ariff_dc.py` is the only place for Ariff native bodies.
- Distinct ids `voh_load`/`vol_load` (RS0204 already owns `voh`/`vol` in the same Logic registry).
- LDO not on RS1G parts.
- No `input()`. No Excel / xyflow this wave (A13/A14).

---

## Ticket index

| ID | File | Status | One-line acceptance |
|----|------|--------|---------------------|
| A12-T01 | [A12-T01-ariff-latest-wraps.md](../tickets/A12-T01-ariff-latest-wraps.md) | implemented (R-0003 pending) | thicken DC + new ids + YAML enable + checks |

---

## Out of epic

- Excel merge-center / OneDrive import (A13)
- xyflow / Activepieces (A14)
- LDO suite; copying Ariff Repo into ate/; reopen A01-A11
