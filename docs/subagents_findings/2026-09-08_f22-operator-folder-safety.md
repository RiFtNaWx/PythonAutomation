---
keywords: a15, operator-folder, migrate, psu-protect, ovp, ocp, category-switch, f22
main_idea: Campaign path is Component/Part/Package/Operator/Version. All is view-only. PSU OVP/OCP always ON at DUT-capped defaults, never instrument max.
---

# F22 / EPIC-A15 operator folder + PSU safety (2026-09-08)

## Path

`#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/`

Migrate: `python -m ate.core.migrate_operator_folders --apply`

## Safety

- `psu_setup.power_on_protected`: defaults V+0.3, I+0.1; abs ceil 6 V / 0.5 A
- Unprotected `power_on` raises
- UI banner under Test Database

## Parked

Cloud, mini-scope, circuit viz, drag-drop, A13/A14.
