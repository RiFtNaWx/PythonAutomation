# A05-T01 - Lab-report sheet_map / TestSpec sync + Noise stub

**Epic:** EPIC-A05
**PRD:** PRD-001
**Status:** closed-accepted
**Step:** current: 5 / 5 - R-0003 PASS; sync check green; fail-path proven; restored
**Depends on:** EPIC-A01 closed (OpAmp family load); A02-A04 closed (do not reopen)
**Model (implement):** composer-2.5-fast
**Model (verify/close):** Grok 4.5 high (`cursor-grok-4.5-high`)
**Adversary rule:** R-0003 - implementer is never the verifier

---

## Problem

OpAmp lab workbook, campaign `sheet_map.yaml`, and registered `TestSpec.lab_sheet` values do not agree. Console/report can look complete while Noise has no spec and the map still names drifted excel sheets.

Evidence (2026-09-03 F8):

- Live xlsx test sheets (not Summary/Checklist): `Slew Rate`, `GBW`, `SettlingTime`, `SSSR`, `LSSR`, `ORT`, `NoPhaseReversal`, `VOS`, `PowerOnTime`, `VOL`, `Noise`, `PSRR`, `CMRR`, `AOL`, `EMIRR`
- `ate/tests/opa/stubs.py`: stubs for SSSR/LSSR/NoPhaseReversal/PowerOnTime/EMIRR/PSRR/CMRR/AOL/VOL - **no Noise**
- Automated `lab_sheet` already match live names for Slew Rate / GBW / SettlingTime / ORT / VOS
- External map (`ate/config/bench.yaml` -> `#Test_Database/.../_manifest/sheet_map.yaml`):
  - `SlewRate.excel_sheet: Slew` (live = `Slew Rate`)
  - `PhaseReversal.excel_sheet: PhaseReversal` (live = `NoPhaseReversal`)
  - `PowerOnTime.excel_sheet: PowerOn` (live = `PowerOnTime`)
  - `VOHL.excel_sheet: VOHL` (live = `VOL`)
  - additional map entries claim sheets not on live workbook (e.g. Iq / Ib / Isc / IOS / Inoise / SlewTemp)
- No runnable check fails today if Noise is missing or map says `Slew`

---

## Acceptance

WHEN the OpAmp lab-report sync check runs against the active campaign workbook + `sheet_map` + registered OpAmp `TestSpec.lab_sheet` values, THE SYSTEM SHALL FAIL if (1) a workbook test sheet (excluding Summary and Checklist) has no matching `TestSpec.lab_sheet`, OR (2) a registered `lab_sheet` is missing from the workbook, OR (3) a `sheet_map` `excel_sheet` value disagrees with the live xlsx sheet name it claims to map (including claiming a sheet that is not on the workbook).

WHEN a workbook test sheet such as Noise previously had no matching spec, THE SYSTEM SHALL list it in the console via a registered stub (RuntimeError OK) and/or explicit sync-check listing - inventing a Noise measurement suite is not required.

WHEN the shipped self-check is run after the honest fix, THE SYSTEM SHALL pass against the live RS622 workbook + corrected map + stubs that cover every live test sheet.

WHEN Noise registration is removed (or map `excel_sheet` is forced back to `Slew`), THE SYSTEM SHALL fail the sync check (adversary must demonstrate fail-path, not only green).

---

## Why it is not a one-liner

Trap: only adding a Noise stub while `sheet_map` still says `Slew` / `PowerOn` / `VOHL` - check looks incomplete. Trap: rewriting map names without a runnable check that fails on drift. Trap: inventing full Noise/PSRR suites to "cover" sheets. Trap: green-passing by ignoring map orphans (Iq/Ib/...) that claim sheets not on the live xlsx. Trap: building a new paste framework for Slew/GBW (out of ticket).

---

## Files likely touched

- `C:\Users\OoiJianHong\#Test_Database\OpAmp\RS622\TTSOP8\Version_1\_manifest\sheet_map.yaml` - fix `excel_sheet` drifts; remove or stop claiming orphans not on live xlsx
- `ate/tests/opa/stubs.py` - add Noise stub (`lab_sheet="Noise"`, same RuntimeError pattern)
- `ate/core/check_lab_report_sync.py` (preferred sibling) **or** extend `ate/core/check_family_load.py` - runnable invariant for (1)(2)(3); print missing sheets
- `ate/config/bench.yaml` - read only for workbook / sheet_map paths (edit only if path resolution is broken)
- Optional one-line note in `docs/ATE_PLUGIN.md` if family authors need to know lab_sheet must match live xlsx

Do **not** implement Noise/PSRR/CMRR/AOL measurement bodies. Do **not** wire Slew/GBW paste. Do **not** reopen A01-A04. Do **not** slice Level / Logic report sync / wizard.

---

## Step

```
Step: current: 5 / 5 - sync check green; fail-path proven; worker restart if idle
```

Suggested steps for the runner (update the counter as you go):

1. Add Noise stub in `ate/tests/opa/stubs.py` (`lab_sheet="Noise"`)
2. Fix `sheet_map.yaml` `excel_sheet` drifts to live names; handle map-only orphans so check cannot green-pass on missing sheets
3. Ship runnable sync check (sibling preferred) that fails on (1)(2)(3) and lists missing sheets
4. Prove fail-path: temporarily drop Noise or set `Slew` again -> check fails; restore -> check passes
5. Keep `python -m ate.core.check_family_load` green; idle worker restart only if registry/UI needs it; leave verify notes for adversary

---

## Agent prompt

> Implement EPIC-A05 ticket A05-T01 only (OpAmp lab-report / sheet_map / TestSpec sync + Noise stub). Repo: PythonAutomation. A01-A04 stay closed. Do not implement other epics.
>
> **Goal:** Live workbook test sheet names, `sheet_map.excel_sheet`, and OpAmp `TestSpec.lab_sheet` agree. A runnable check FAILS on mismatch or missing Noise. Stub OK for Noise. No full Noise/PSRR suites. No Slew/GBW paste.
>
> **Shell:** if you run Python, set working_directory to `C:\Users\OoiJianHong\EUGENE~1\PYTHON~1` (apostrophe path trap).
>
> **Do:**
> 1. Register a Noise stub in `ate/tests/opa/stubs.py` with `lab_sheet="Noise"` (same RuntimeError yellow/manual pattern as other stubs).
> 2. Fix campaign `sheet_map.yaml` (path from `ate/config/bench.yaml`) so every claimed `excel_sheet` matches a live xlsx sheet name. At minimum: `Slew` -> `Slew Rate`, `PhaseReversal` -> `NoPhaseReversal`, `PowerOn` -> `PowerOnTime`, `VOHL` -> `VOL`. Entries that claim sheets not on the live workbook (Iq/Ib/Isc/IOS/Inoise/SlewTemp or similar) must not remain as green-pass claims - remove them from the map or exclude them only with an explicit honest mechanism the check still enforces for in-workbook claims.
> 3. Ship `python -m ate.core.check_lab_report_sync` (preferred) or extend `python -m ate.core.check_family_load` so the check: reads live workbook sheet names + sheet_map + OpAmp registered `lab_sheet` values; **fails** if (1) workbook test sheet (not Summary/Checklist) has no matching lab_sheet, OR (2) registered lab_sheet missing from workbook, OR (3) sheet_map excel_sheet disagrees with live name / missing from workbook; **lists** missing sheets on console.
> 4. Self-prove fail-path once: without committing the broken state - temporarily remove Noise stub or set excel_sheet back to `Slew` and confirm the check fails; restore and confirm pass.
> 5. Keep prior `check_family_load` green. Brief doc note only if needed.
>
> **Constraints:**
> - Source of truth = live xlsx sheet names. Do not invent alternate names.
> - Do **not** implement Noise/PSRR/CMRR/AOL/EMIRR measurement algorithms.
> - Do **not** add Slew/GBW paste (no new place_* framework; SlewRate map has no photo anchors).
> - Do **not** reopen A01-A04. Do not slice Level / Logic report sync / wizard. No GitHub Issues.
> - YAGNI / ponytail: fewest files; stub + map fix + one check module.
>
> **Out of ticket:** full Noise/PSRR suites; Slew/GBW paste; Level; wizard; dual-stack delete; GitHub Issues; A01-A04 reopen.
>
> **Model:** implement with composer-2.5-fast. Do not self-close; a different Grok 4.5 high run verifies (R-0003).
>
> After edits that affect the worker registry, if idle, restart via `restart_ate_worker.bat` per workspace rule. Tell operator Ctrl+F5 if console test list changed.

---

## Verify (different run - R-0003)

Implementer must not run this as the close gate. Verifier (Grok 4.5 high) runs:

1. **Runnable pass:** shipped sync check against live workbook + map + OpAmp registry - must pass after the fix.
2. **Runnable fail-path (mandatory):** temporarily unregister/omit Noise **or** set map `excel_sheet` to `Slew` instead of `Slew Rate` - check **must fail** and list the gap; restore after. Do not close if only the happy path was shown.
3. **Static:** `stubs.py` has Noise with `lab_sheet="Noise"`; map drifts above are fixed; no new Noise/PSRR measurement body; no new Slew/GBW place_* paste path.
4. **Console:** OpAmp `list_tests` / Run list includes Noise (stub) after idle worker restart if needed.
5. Prior: `python -m ate.core.check_family_load` still green.

Close only if acceptance WHEN/SHALL statements hold; then update epic ticket index status in the same action.
