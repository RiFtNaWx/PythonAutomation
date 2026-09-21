---
keywords: [demo, tomorrow, sim, pyvisa, tutorial, install, eugene, cin, cpd, sts-pdf, fill-excel, sidecar]
main_idea: Tomorrow DEMO is install + DEMO (SIM) + STS PDF. SelectedTests now reads Setup list only (Tests-page ticks no longer double-run). SIM fill writes *_demo.xlsx and skips photo paste so the live lab book stays clean.
---

# 2026-09-13 Tomorrow DEMO E2E

PREFLIGHT: PARTIAL. Reuse: 2026-09-13_demo-sts-pdf-sim, 2026-09-13_rs1g07-demo-sts-pipeline, 2026-09-13_demo-building-plan-families. Spawn: skip.

## Objective

Show everyone how to use the console: install, backend+frontend, Eugene extras (cin/cpd), report fill/generate, fake PyVISA (0/typ values OK), final STS PDF.

## Gaps found

1. Tests-page `.test-item` checkboxes were included in START/DEMO ids (each slot ran twice).
2. `params.part` defaulted to `rs622` when part_key was missing (header leftover).
3. Session-end fill/photo paste could write the live lab xlsx during SIM.
4. Slew `Cnt=0` wait could stall 6s then raise on a fake scope.
5. No single install+walkthrough page.

## Shipped

- `selectedTests()` / loadTests listeners scoped to `#test-list`
- `currentPartKey()` from campaign, not rs622
- SIM fill -> `workbook/*_demo.xlsx`; skip photo paste when instrument_map is `SIM::`
- `wait_slew_statistics` returns immediately on `scope.simulated`
- `docs/DEMO.md` (install + 10 min walk: Eugene, Logic, RS1G07 SC70-5, DEMO, STS PDF)
- Button **DEMO (SIM)**; cache `app.js?v=20260913demo3`

## Proof

```
python -m ate.core.check_sim_run
python -m ate.core.check_demo_families
python -m ate.core.check_ui_contract
python -m ate.core.check_session_values
python -m ate.core.check_launch
```

Live DEMO 22:05:35 (`session_2026-09-13_220535`): Eugene RS1G07 SC70-5, model RS1G07, 6 unique tests, Total 6 Pass 6 Fail 0, `sessions/datalog.pdf`, sidecar `RS1G07XC5_Lab_Report_demo.xlsx`.

Walk: [docs/DEMO.md](../DEMO.md). Presenter: Ctrl+F5 on 5174 (cache `?v=20260913demo3`).

## Does not prove

- Live USB START
- Real DMM numbers
- Full paste.values coverage on RS1G07 SOT23 (SC70-5 has ICC C6 only)
