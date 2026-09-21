# A06-T01 - LA-1 BUFFER wraps (SSSR / LSSR / NPR)

**Epic:** EPIC-A06
**PRD:** PRD-001
**Status:** closed-accepted
**Step:** current: 6 / 6 - R-0003 PASS; epic Mode B closed
**Depends on:** EPIC-A05 closed (honest sheet_map / lab_sheet); A01-A04 closed, not reopened
**Model (implement):** composer-2.5-fast
**Model (verify/close):** Grok 4.5 high (`cursor-grok-4.5-high`)
**Adversary rule:** R-0003 - implementer is never the verifier

---

## Problem

OpAmp BUFFER companions Small/Large Signal Step Response and No Phase Reversal are still RuntimeError stubs while LabAutomation-1 already has runnable recipes. Operator Run looks complete but cannot produce workbook screenshots for those sheets.

Evidence (2026-09-03 F11 / scale finding):

- `ate/tests/opa/stubs.py` ~31-33: `_stub("Small Signal Step Response", "SSSR", "BUFFER")`, `_stub("Large Signal Step Response", "LSSR", "BUFFER")`, `_stub("Phase Reversal Protection", "NoPhaseReversal", "BUFFER")` -> ids `small_signal_step_response` / `large_signal_step_response` / `phase_reversal_protection` raise RuntimeError on run
- LA-1 source (prefer this): `C:\Users\OoiJianHong\Downloads\LabAutomation-1\LabAutomation-1\Eugene\RS622\opa_tests.py` - `test_SSR`, `test_LSR`, `test_NPR` (SSR newer than repo-root `opa_tests.test_SSR`)
- Campaign `sheet_map.yaml`: `SmallSignalStep` / `LargeSignalStep` already have `paste.photos` grids (`excel_sheet: SSSR` / `LSSR`); `PhaseReversal` `excel_sheet: NoPhaseReversal` has **no** paste photos; GBW has unused A45 grid
- ATE paste pattern already exists: `ate/reporting/lab_report.py` `embed_photo` + `place_ort_photos` / `place_settling_photos` + `save_named_screenshot` / `ensure_screenshot_dir` (see `ate/tests/opa/settling.py`, `ort.py`)
- LA-1 / legacy recipes may use `input("Press Enter...")` - that hangs the ATE worker console; must not ship

---

## Acceptance

WHEN the operator runs OpAmp tests with ids covering SSSR / LSSR / NoPhaseReversal (current stub ids `small_signal_step_response`, `large_signal_step_response`, `phase_reversal_protection`, or stable renames that keep the same `lab_sheet` values) with an open instrument session, THE SYSTEM SHALL invoke the corresponding LabAutomation-1 recipe path (`test_SSR` / `test_LSR` / `test_NPR` logic, copied into the repo or thin-wrapped) and SHALL NOT raise the A05-era stub `RuntimeError`.

WHEN those runs complete a capture step, THE SYSTEM SHALL save screenshots under Test_Database (campaign screenshot dirs / folders consistent with sheet_map `SmallSignalStep` / `LargeSignalStep` / `PhaseReversal`).

WHEN `sheet_map` has photo anchors for SSSR or LSSR, THE SYSTEM SHALL paste via the existing `lab_report.embed_photo` pattern (Settling/ORT family - thin `place_*` helper OK; do not invent a second paste framework).

WHEN `sheet_map` has no photo anchors for NoPhaseReversal / PhaseReversal, THE SYSTEM SHALL still save screenshots and SHALL NOT fail the run solely for missing paste anchors.

WHEN GBW screenshots already exist on disk and sheet_map has GBW A45 photo anchors, THE SYSTEM MAY paste them in this ticket only if reuse of existing helpers is cheap; inventing a second paste framework is out.

WHEN the ATE worker executes these three run paths, THE SYSTEM SHALL NOT call blocking `input()` (use ATE operator gate / Continue dock, or non-blocking auto-capture after settle like Settling).

WHEN `python -m ate.core.check_family_load` and `python -m ate.core.check_lab_report_sync` run after the change, THE SYSTEM SHALL stay green against the live RS622 workbook + map (`lab_sheet` values `SSSR` / `LSSR` / `NoPhaseReversal` remain registered).

WHEN PowerOn / Noise / PSRR / CMRR / AOL / VOL / EMIRR remain without LA-1 RS622 wrap in this ticket, THE SYSTEM SHALL leave those stubs as stubs.

---

## Why it is not a one-liner

Trap: deleting stubs without a recipe path (console green list, run still broken). Trap: wrapping weaker repo-root `opa_tests.test_SSR` instead of LA-1. Trap: leaving `input()` so the worker hangs with no Continue dock. Trap: inventing full PSRR/Noise suites or copying whole LabAutomation-1. Trap: replacing ATE-native slew/settling/ORT/GBW with LA-1 `test_sr` / `test_settlingTime` / `test_ORT` / `test_gbw`. Trap: requiring NPR paste when sheet_map has no anchors. Trap: inventing a second Excel / DataLogger system.

---

## Files likely touched

- `ate/tests/opa/stubs.py` - remove only the three BUFFER stubs (SSSR/LSSR/NoPhaseReversal); keep PowerOn/Noise/PSRR/...
- `ate/tests/opa/` - new thin modules (e.g. `sssr.py`, `lssr.py`, `npr.py`) with `_run` + `register(TestSpec(...))`; same `lab_sheet` / BUFFER `fixture_mode`
- `ate/tests/opa/__init__.py` - import new modules; stop relying on stubs for those three
- Vendored/copied LA-1 recipe body (inside the new modules or a small sibling) - prefer LA-1 `test_SSR`/`test_LSR`/`test_NPR` over Downloads import at runtime
- `ate/reporting/lab_report.py` - reuse `embed_photo` / `save_named_screenshot` / `ensure_screenshot_dir`; add thin place helpers for SSSR/LSSR anchors if Settling-style hardcode is cheapest
- Optional: `ate/tests/opa/gbw.py` - paste-only stretch using A45 grid; do not replace `measure_gbw`

Do **not** wrap/replace slew/settling/ort/gbw measurement bodies. Do **not** implement PowerOn/Noise/PSRR. Do **not** copy whole LabAutomation-1. Do **not** reopen A01-A05. Do **not** slice RS1G / Lim / Level.

**Map ids (keep lab_sheet stable):**

| LA-1 function | lab_sheet | sheet_map key | Paste |
|---------------|-----------|---------------|-------|
| `test_SSR` | `SSSR` | `SmallSignalStep` | yes (photo grid) |
| `test_LSR` | `LSSR` | `LargeSignalStep` | yes (photo grid) |
| `test_NPR` | `NoPhaseReversal` | `PhaseReversal` | no (screenshots only) |

---

## Step

```
Step: current: 6 / 6 - R-0003 PASS; epic Mode B closed
```

Suggested steps for the runner (update the counter as you go):

1. [x] Copy/thin-wrap LA-1 `test_SSR` / `test_LSR` / `test_NPR` into `ate/tests/opa/` modules; strip `input()`; use ATE gate or auto-capture
2. [x] Register TestSpecs with lab_sheets SSSR/LSSR/NoPhaseReversal; remove matching stubs; wire `__init__.py`
3. [x] Save screenshots under Test_Database via `ensure_screenshot_dir` / `save_named_screenshot` / capture_jpeg (Settling pattern)
4. [x] Paste SSSR/LSSR via `embed_photo` + sheet_map anchors; NPR screenshots only
5. [x] Optional MAY: GBW A45 paste if screenshots on disk and no second framework (skipped - not claimed)
6. [x] Prove `check_family_load` + `check_lab_report_sync` green; idle worker restart if registry changed; R-0003 PASS (finding `docs/subagents_findings/2026-09-03_a06-t01-r0003-verify-pass.md`)

---

## Agent prompt

> Implement EPIC-A06 ticket A06-T01 only (LA-1 BUFFER wraps SSSR/LSSR/NPR). Repo: PythonAutomation. A01-A05 stay closed. Do not implement other epics.
>
> **Goal:** Replace SSSR/LSSR/NoPhaseReversal RuntimeError stubs with thin ATE wraps of LabAutomation-1 recipes. Screenshots to Test_Database. Paste where sheet_map photo anchors exist. No hanging `input()`. Keep family_load + lab_report_sync green.
>
> **Shell:** if you run Python, set working_directory to `C:\Users\OoiJianHong\EUGENE~1\PYTHON~1` (apostrophe path trap).
>
> **Source of truth for recipes:** `C:\Users\OoiJianHong\Downloads\LabAutomation-1\LabAutomation-1\Eugene\RS622\opa_tests.py` functions `test_SSR`, `test_LSR`, `test_NPR`. Prefer LA-1 over repo-root `opa_tests.test_SSR` / `test_LSR`. Copy or thin-wrap into the ATE package - do not depend on the Downloads path at runtime, and do not vendor the whole LA-1 tree.
>
> **Do:**
> 1. Add OpAmp TestSpec modules under `ate/tests/opa/` that call the LA-1 recipe logic for SSR->SSSR, LSR->LSSR, NPR->NoPhaseReversal. Keep `fixture_mode="BUFFER"` and `lab_sheet` values `SSSR` / `LSSR` / `NoPhaseReversal`. Stable ids may keep stub names or shorten; do not break sync check sheet coverage.
> 2. Remove those three stubs from `ate/tests/opa/stubs.py`. Leave PowerOnTime / Noise / PSRR / CMRR / AOL / VOL / EMIRR stubs alone.
> 3. Wire `ate/tests/opa/__init__.py` imports so `load_family("opamp")` registers the new wraps.
> 4. On run: capture scope screenshots into Test_Database (reuse `ensure_screenshot_dir` / `save_named_screenshot` / `capture_jpeg` like Settling/ORT). Folders should align with sheet_map (`SmallSignalStep` / `LargeSignalStep` / `PhaseReversal`).
> 5. Paste SSSR and LSSR into the lab workbook via `lab_report.embed_photo` using existing sheet_map photo anchors (Settling/ORT pattern; thin place_* helper OK). For NoPhaseReversal: screenshots required; paste not required (no map photos).
> 6. Replace any `input()` with ATE operator gate (runner Continue / `_ask_operator` style) or non-blocking auto-capture after settle. Worker must not hang on stdin.
> 7. Optional MAY only: if GBW screenshots already exist and sheet_map A45 anchors are enough, paste with existing helpers - do not invent a second paste framework; skip if not cheap.
> 8. Keep `python -m ate.core.check_family_load` and `python -m ate.core.check_lab_report_sync` green.
>
> **Constraints:**
> - Do **not** replace ATE-native `slew.py` / `settling.py` / `ort.py` / `gbw.py` (`measure_gbw`) with LA-1 `test_sr` / `test_settlingTime` / `test_ORT` / `test_gbw`.
> - Do **not** implement PowerOn / Noise / PSRR / CMRR / AOL / VOL / EMIRR bodies.
> - Do **not** replace DataLogger or invent a second Excel system.
> - Do **not** copy whole LabAutomation-1. Do **not** reopen A01-A05. No GitHub Issues. No Level / RS1G / Lim.
> - YAGNI / ponytail: fewest files; one wrap path for all three.
>
> **Out of ticket:** PowerOn/Noise/PSRR suites; slew/settling/ORT/GBW body replacement; DataLogger wholesale; whole LA-1 copy; GitHub Issues; A01-A05 reopen.
>
> **Model:** implement with composer-2.5-fast. Do not self-close; a different Grok 4.5 high run verifies (R-0003).
>
> After edits that affect the worker registry, if idle, restart via `restart_ate_worker.bat` per workspace rule. Tell operator Ctrl+F5 if console test list changed.

---

## Verify (different run - R-0003)

Implementer must not run this as the close gate. Verifier (Grok 4.5 high) runs:

1. **Static:** stubs.py no longer registers RuntimeError for SSSR/LSSR/NoPhaseReversal; new wrap modules call LA-1 recipe logic (copied/thin wrap); PowerOn/Noise/PSRR stubs remain; no wholesale LA-1 tree copy; ATE-native slew/settling/ort/gbw bodies not replaced.
2. **Static hang check:** no bare `input(` in the new ATE run path for these three tests.
3. **Paste:** SSSR/LSSR use `embed_photo` (or thin place_* calling it) with sheet_map-style anchors; NPR does not require paste.
4. **Runnable:** `python -m ate.core.check_family_load` green; `python -m ate.core.check_lab_report_sync` green.
5. **Registry / console:** after idle worker restart if needed, OpAmp `list_tests` still lists the three BUFFER tests with lab_sheets SSSR/LSSR/NoPhaseReversal and they are not stub RuntimeError callables.
6. Optional GBW paste: if claimed, prove it uses existing helpers + A45 anchors; if not shipped, do not fail the ticket.

Close only if acceptance WHEN/SHALL statements hold; then update epic ticket index status in the same action.
