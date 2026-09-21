---
keywords: e2e, playwright, uacc, operator-flow, family-rail, demo, start-gate, unassigned, f22, workflow
main_idea: Live 2026-09-08 click-through -- family rail and START gate match PRD-001; default campaign still lands on empty _unassigned after F22 migrate, so operators can miss the live Eugene/Ariff/ChangThong workbooks. Hardware START not proven (VISA {}).
---

# Operator flow E2E review (2026-09-08)

PREFLIGHT: PARTIAL. Reuse: console-fluency, new-product-demo, f22-operator-folder-safety, product-class-operator. Spawn: skip (parent clicked).

## How

Playwright `http://127.0.0.1:5174`. Worker ping 0.2.16 after idle restart (was 0.2.15). UACC listed Explorer `Version_1` after Open DB folder; ATE Worker minimized. No MSO/PSU/AWG/DMM in Discover.

## Match (intended idea)

- Left rail switches tests + fixtures + brand (OpAmp 17 + G11; Logic YAML-filtered; Analog SW LIM_RS2323; Level stub; Demo `demo_probe`).
- START disabled until Open Session. Open Session with `{}` -> `Required instrument(s) not found: ['MSO']`.
- DEMO: 17 mock steps, `sessions/session_2026-09-08_144320.json` under Eugene, Results table, sheet_map ORT grid, lab xlsx not stamped.
- RS29511=7 Soo, RS1G08=12 Ariff, RS0204=16 + VCCA/VCCB.
- Import family empty and Create folders without part both alert.
- PSU protect exists in `psu_setup.power_on_protected` (not live-fired).

## Gaps vs muscle memory

1. Family rail / boot can Apply `_unassigned` (empty). Live RS622 workbook is `Eugene/Version_1`. Cause: `bench.yaml` still 4-level; `operators[0]` sorts `_unassigned` first.
2. Top-right Operator picker vs Operator folder can disagree (Lim picker + Ariff/Eugene/Soo folder). Analog SW Lim empty; SeeLim has the xlsx.
3. `applyTestDefaults` returns early when no tests ticked, so Advanced bench checkbox can stay CSS-hidden.
4. DEMO does not fill Run timeline (0/0). Hardware Continue path untested.
5. "Map coverage OK: 0" is a false-OK string. Photo hint still names ORT on Logic campaigns.

## Can we achieve the job?

Campaign + DEMO + Results: yes if Operator folder is the person who owns the workbook. Full bench START: not on this host today.

## Next

Point `bench.yaml` + rail default at person folders with a sheet_map; skip `_unassigned`. Then Discover on the instrumented bench.
