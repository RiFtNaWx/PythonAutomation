# EPIC-A15 - Operator folder + category switch + PSU safety

**PRD:** PRD-001 F22
**Status:** implemented
**Do not reopen:** A01-A12. A13 Excel merge-center and A14 xyflow stay parked.

## Goal

1. Campaign path inserts person folder before Version:
   `#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/`
2. RUN-IC class / Component change loads the matching suite (or stub folders only).
3. PSU OVP/OCP always ON, DUT-capped (Vset+0.3 V, Iset+0.1 A), never DP832 30 V / 3 A.

## Tickets

| ID | Seam |
|----|------|
| A15-T01 | Operator path + migrate + UI cascade + session identity |
| A15-T02 | Category / component switches family suite in one click |
| A15-T03 | power_on_protected golden + readback; ban unprotected power_on |

## Parked (not this epic)

- Cloud sync
- Mini-scope / CSV chart
- Circuit drawing
- Drag-drop waves
- Comparator / Power measurement bodies

## Checks

```
python -m ate.core.check_operator_tree
python -m ate.core.check_new_product
python -m ate.core.check_family_load
python -m ate.drivers.check_psu_protect
python -m ate.core.migrate_operator_folders --apply
```
