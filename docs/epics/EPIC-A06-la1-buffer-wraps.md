# EPIC-A06 - LA-1 BUFFER wraps into workbook use cases

**PRD:** [PRD-001-ate-multi-product-platform](../prd/PRD-001-ate-multi-product-platform.md)
**Repo:** PythonAutomation
**Status:** closed-accepted
**Sliced:** 2026-09-03 (epic-agent Mode A; F11 / F12)
**Closed:** 2026-09-03 (R-0003 Mode B; F13)
**Tier:** capability (measurement recipes) + visible surface (Test_Database screenshots / workbook paste)
**Depends on:** EPIC-A05 closed (honest sheet_map / lab_sheet); A01-A04 closed, not reopened
**Blocks:** none hard; later PowerOn / Noise / PSRR stay parked
**Appetite:** 1 wave
**GitHub Issues:** do not open unless founder opts in

---

## Buyer-visible outcome

Operator with an open instrument session can run Small Signal Step Response (SSSR), Large Signal Step Response (LSSR), and No Phase Reversal (NPR / NoPhaseReversal) and get real LabAutomation-1 recipes (not A05-era RuntimeError stubs). Screenshots land under Test_Database. When `sheet_map` already has photo anchors (SSSR / LSSR), paste uses the existing `lab_report.embed_photo` family (same pattern as ORT / Settling). Workbook remains the characterization SoT; DataLogger stays the pass-fail log (do not replace wholesale).

---

## Acceptance (from PRD)

> WHEN the operator runs SSSR, LSSR, or NPR (NoPhaseReversal) with an open instrument session, THE SYSTEM SHALL invoke the corresponding LabAutomation-1 recipe path via a thin ATE wrap (not raise the A05-era RuntimeError stub) and SHALL save screenshots under Test_Database. WHEN `sheet_map` has photo anchors for that test, THE SYSTEM SHALL paste via the existing `lab_report.embed_photo` pattern (same family as ORT/Settling). WHEN GBW screenshots are already captured on disk and sheet_map has GBW photo anchors (A45 grid), THE SYSTEM MAY paste them in the same epic if it reuses existing helpers without inventing a second paste framework. WHEN PSRR / CMRR / AOL / VOL / EMIRR have no LA-1 RS622 recipe, THE SYSTEM SHALL leave those stubs as stubs.

**Ticket-level sharpening (this slice):**

- Stub ids `small_signal_step_response` / `large_signal_step_response` / `phase_reversal_protection` SHALL no longer raise the stub `RuntimeError` on run.
- Run path SHALL call LA-1 `test_SSR` / `test_LSR` / `test_NPR` recipe logic (copied into repo or thin-wrapped; prefer LA-1 over weaker repo-root `opa_tests.test_SSR`).
- No bare `input()` in the ATE worker run path (hangs the console). Use ATE operator gate (`_ask_operator` / Continue dock) or non-blocking auto-capture after settle (Settling pattern).
- `python -m ate.core.check_family_load` and `python -m ate.core.check_lab_report_sync` SHALL stay green.

---

## Design constraints

- Source recipes: `C:\Users\OoiJianHong\Downloads\LabAutomation-1\LabAutomation-1\Eugene\RS622\opa_tests.py` (`test_SSR` -> SSSR, `test_LSR` -> LSSR, `test_NPR` -> NoPhaseReversal). Prefer thin wrap / copy over rewriting bodies. LA-1 SSR is newer than repo-root `opa_tests.test_SSR` - do not prefer the weaker legacy path.
- Keep ATE-native: `slew.py`, `settling.py`, `ort.py`, `gbw.py` (`measure_gbw`). Do not replace them with LA-1 `test_sr` / `test_gbw` / `test_settlingTime` / `test_ORT`.
- Two reports: LA-1 DataLogger / `RS622_results.xlsx` = pass-fail log; ATE `RS622XK_Lab_Report_TTSOP.xlsx` + sheet_map = characterization workbook (founder SoT). Do not replace DataLogger wholesale. Do not invent a second Excel system.
- sheet_map already has SSSR/LSSR photo anchors (`SmallSignalStep` / `LargeSignalStep` paste grids). `PhaseReversal` / NoPhaseReversal map has no paste photos - wrap + Test_Database screenshots still required; paste only where anchors exist.
- Optional same epic: GBW `place_*` using existing sheet_map A45 grid if screenshots already on disk and no second framework.
- Do not reopen A01-A05. Do not slice RS1G07/14/08, Lim RS2323, PowerOn MOSFET, Noise flicker, or full PSRR/CMRR/AOL/VOL/EMIRR suites.
- Do not copy the whole LabAutomation-1 tree into this repo.

---

## Ticket index

| ID | File | Status | One-line acceptance |
|----|------|--------|---------------------|
| A06-T01 | [A06-T01-la1-buffer-wraps.md](../tickets/A06-T01-la1-buffer-wraps.md) | closed-accepted | SSSR/LSSR/NPR stubs -> LA-1 wraps; screenshots to Test_Database; paste where sheet_map anchors exist; no hanging `input()`; family_load + lab_report_sync green |

**Ponytail:** one ticket. Wrap + screenshot + paste share one run path and the same three BUFFER ids. Splitting paste into a second ticket would race stubs half-replaced. Optional GBW A45 paste is a MAY stretch inside T01, not a second ticket.

---

## File contention

| Area | Tickets | Note |
|------|---------|------|
| `ate/tests/opa/stubs.py` | T01 | Remove SSSR/LSSR/NoPhaseReversal RuntimeError stubs (keep PowerOn/Noise/PSRR/... stubs) |
| `ate/tests/opa/` new wrap modules (e.g. `sssr.py` / `lssr.py` / `npr.py`) + `__init__.py` | T01 | Register same lab_sheets; call LA-1 recipe (copied/thin wrap) |
| `ate/reporting/lab_report.py` | T01 | Reuse `embed_photo` / `save_named_screenshot` / `ensure_screenshot_dir` / Settling-style `place_*`; add thin `place_sssr` / `place_lssr` (or sheet_map-driven helper) only if needed |
| External `sheet_map.yaml` photo anchors | T01 read | SSSR / LSSR photo grids; PhaseReversal no photos; GBW A45 optional |
| `ate/tests/opa/slew.py`, `settling.py`, `ort.py`, `gbw.py` | **out** (except optional GBW paste caller) | Do not replace ATE-native bodies with LA-1 |
| DataLogger / whole LA-1 tree | **out** | |

---

## Out of epic

- RS1G ingest; Lim RS2323 family
- PowerOn MOSFET; Noise flicker / noise_bucket
- Full PSRR / CMRR / AOL / VOL / EMIRR measurement suites
- Replacing ATE-native slew / settling / ORT / GBW with LA-1
- DataLogger replacement; second Excel system
- Copying whole LabAutomation-1 tree
- Level; wizard; GitHub Issues; reopening A01-A05

---

## Completeness (Mode B - after T01 closes)

**COMPLETE / closed-accepted** 2026-09-03. Finding: `docs/subagents_findings/2026-09-03_a06-t01-r0003-verify-pass.md`.

Re-derived from code + runnable checks (not ticket checkboxes):

1. [x] Static / registry: `sssr` / `lssr` / `no_phase_reversal` in `ate/tests/opa/buffer_steps.py` (not stub RuntimeError); PowerOn/Noise/PSRR stubs remain in `stubs.py`.
2. [x] Run path: LA-1 recipe logic in `_run_sssr` / `_run_lssr` / `_run_npr`; folders `SmallSignalStep` / `LargeSignalStep` / `PhaseReversal`; no Downloads import.
3. [x] Paste: `place_sssr_photos` / `place_lssr_photos` -> `_place_buffer_step_photo` -> `embed_photo`; NPR screenshots only.
4. [x] No `input()` in `buffer_steps.py`; SSSR overshoot via `scope.query(":MEASure:ITEM? OVERshoot,CHAN2")`.
5. [x] `venv\Scripts\python.exe -m ate.core.check_family_load` and `-m ate.core.check_lab_report_sync` EXIT 0; live RPC `list_tests` includes the three with lab_sheets SSSR/LSSR/NoPhaseReversal.
6. [x] Recipe path present (not stub-delete-only). ATE-native slew/settling/ort/gbw bodies unchanged. Optional GBW A45 paste not shipped (MAY; not fail).
