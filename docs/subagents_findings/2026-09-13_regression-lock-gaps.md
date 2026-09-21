---
keywords: regression-lock, get_context, selectedTests, sim-demo, rs622, input, Ariff, A91, operator-all, power_on_protected, dmm, applyDb, false-green, slew-cnt, visa-poison
main_idea: Most prior ATE bugs have production fixes plus at least one fail-closed check; gaps are SIM photo-paste skip, server rs622 fallback, repo-wide input/vendor scans, Instruments.dmm attribute, and check_family_load listing without run proof.
---

# 2026-09-13 Regression lock audit (14 prior bugs)

Audit only -- no code changes. Thoroughness: medium.

## HIT locks (check fails if bug returns)

| # | Bug | Production lock | Check lock |
|---|-----|-----------------|------------|
| 1 | `get_context` UnboundLocalError in `run_sequence` | `ate/core/runner.py:14` module import; uses `get_context()` at `:335`, `:787` -- no inner `from ate.core.database import get_context` in `run_sequence` | `ate/core/check_sim_run.py:14-27` AST ban; `ate/core/check_visa.py:114-121` duplicate |
| 2 | START/DEMO double-run (Tests-page checkboxes) | `ate/ui/web/app.js:652-653` `selectedTests()` scoped to `#test-list` | `ate/core/check_ui_contract.py:176-179` rejects `.test-item input:checked` without `#test-list` |
| 3 | SIM fill live xlsx (partial) | `ate/core/database.py:1024-1035` skip `paste_session_photos` when SIM; `fill_workbook_from_report(demo=sim)`; `ate/reporting/session_values.py:134-139` `*_demo.xlsx` | `ate/core/check_session_values.py:342-356` demo sidecar + live xlsx untouched |
| 7 | Hardcoded A91 photo maps | `ate/reporting/lab_report.py:12,97,139,201` via `photo_anchor()`; `ate/reporting/photo_layout.py:10` doc ban | `ate/reporting/check_photo_layout.py:39-42` bans `_SSSR_PHOTO_ANCHORS` etc. |
| 8 | Operator All can write | `ate/core/database.py:46,119-126,734` `require_write_operator`; `ate/ui/web/app.js:329-336` | `ate/core/check_operator_tree.py:27-38,118-121`; `ate/core/check_ui_contract.py:140-151` |
| 9 | Unprotected `power_on` / DP832 30V 3A | `psu_setup.py` via `ate/drivers/check_psu_protect.py:49-54`; all `ate/tests/**` use `power_on_protected` only | `ate/drivers/check_psu_protect.py:22-60` |
| 11 | Combo change auto `applyDb` | `ate/ui/web/app.js:2407-2444` combo `change` logs only; `applyDb` on `btn-apply-db` `:2448` | `ate/core/check_ui_contract.py:184-191` |
| 13 | Slew Cnt=0 stall on SIM scope | `ate/drivers/mso5072.py:201-202` early return when `scope.simulated`; `:204` `:RUN` before accumulate | `ate/core/check_sim_run.py:71-75`; `ate/drivers/check_slew_capture_run.py:101-106,135-137` |
| 14 | `wait_slew` / `VI_ERROR_SYSTEM_ERROR` reopen | `ate/core/runner.py:836,893-905,961,988-993` poison detect + MSO reopen retry | `ate/drivers/check_slew_capture_run.py:149-163` |

## GAPS (add smallest assertion to existing `check_*.py`)

| # | Bug | Why GAP | Smallest assertion (parent) |
|---|-----|---------|----------------------------|
| 3 | SIM session-end photo paste | Production skips photos on SIM (`database.py:1025`) but no check asserts it | `check_sim_run.py` (or `check_session_values.py`): after SIM `run_sequence`, `paste_session_photos` was not called / live xlsx has no embedded images |
| 4 | `params.part` defaults `rs622` | `ate/worker/server.py:44,245,497` still `or "rs622"`; `RunParams` default `ate/core/runner.py:48`. UI fixed: `app.js:646-649` `currentPartKey()` | `check_sim_run.py` or `check_ui_contract.py`: read `server.py` and `assert 'or "rs622"' not in _build_run_params` (or RPC smoke with empty `part` on RS1G07 ctx must not use rs622 limits) |
| 5 | `input()` in TestSpec / wrap | Locks cover detect fixture, `eugene_cap`, `ariff_dc`, `rs2323` only | `check_add_test.py`: `rglob ate/tests/**/*.py` -- fail on `(?<![\"'\\w])input\\s*\\(` outside docstring-only lines |
| 6 | `import Ariff.*` / `Lim.*` / `Soo.*` | `check_logic_campaign.py:173-206`, `check_open_inventory.py:27-28` (lim file only) | `check_open_inventory.py` or `check_logic_campaign.py`: `rglob ate/tests` fail on `^\\s*(import|from)\\s+(Ariff|Lim|Soo)\\b` |
| 10 | Instruments session missing `dmm` | `ate/instruments/session.py:35,54` sets `self.dmm` | `check_visa.py`: `assert "self.dmm" in session.py` and `Instruments.simulated().dmm is not None` |
| 12 | False-green checks that only list tests | `check_family_load.py:201-312` and `check_mapped_tests.py:52-65` verify registry ids only; run proof is separate | `check_family_load.py`: after id probes, `import subprocess; subprocess.run([sys.executable,"-m","ate.core.check_demo_families"], check=True)` **or** one inline `run_sequence(["cin"], sim=True)` per family stub |

## Per-bug detail

### 1. UnboundLocalError `get_context` (Building plan stuck)

- **(a)** OK. Module-level import `runner.py:14`; `run_sequence` calls `get_context()` at `335`, `787` without re-import.
- **(b)** `check_sim_run.py:14-27`, `check_visa.py:114-121`.
- **(c)** HIT.

### 2. START/DEMO ran Tests-page checkboxes

- **(a)** OK. `app.js:652-653`.
- **(b)** `check_ui_contract.py:176-179`.
- **(c)** HIT.

### 3. SIM session-end fill wrote live lab xlsx

- **(a)** OK. `database.py:1024-1035`; `session_values.py:134-139`.
- **(b)** `check_session_values.py:342-356` covers `*_demo.xlsx` + live unchanged; **no check for photo paste skip on SIM**.
- **(c)** GAP: assert SIM `end_session` does not call `paste_session_photos`.

### 4. `params.part` defaulted to `rs622` when `part_key` missing

- **(a)** Partial. UI uses `currentPartKey()` without rs622 fallback (`app.js:646-649`). Server `_build_run_params` still `or "rs622"` (`server.py:44,245`); `RunParams.part` default `runner.py:48`. `set_context` derives `part_key` from part yaml when present (`database.py:723-731`).
- **(b)** `check_ui_contract.py:180-181` (JS only); `check_sim_run.py:136-139` (stale model on RS1G07, not `params.part`).
- **(c)** GAP: ban `or "rs622"` in `server.py` `_build_run_params`.

### 5. `input()` in TestSpec.run / wrap

- **(a)** OK. No live `input()` calls under `ate/tests/` (only docstring mentions).
- **(b)** `check_test_detect.py:65-67,71-80`; `check_add_test.py:59-60`; `check_logic_campaign.py:170-171`; `check_open_inventory.py:25-26` (rs2323 only).
- **(c)** GAP: repo-wide `ate/tests` scan.

### 6. `import Ariff.*` / `Lim.*` / `Soo.*` in `ate/tests`

- **(a)** OK. No real vendor imports; comments only in `ariff_dc.py`, `rs0204.py`.
- **(b)** `check_logic_campaign.py:173-174,205-206`; `check_open_inventory.py:27-28`.
- **(c)** GAP: scan all `ate/tests/**/*.py`.

### 7. Hardcoded A91 photo maps in `lab_report.py`

- **(a)** OK. Uses `photo_anchor()` from `photo_layout`; no `A91` literals in `lab_report.py`.
- **(b)** `check_photo_layout.py:39-42,55-56`.
- **(c)** HIT.

### 8. Operator All can write (Create folders / DEMO / START)

- **(a)** OK. `WRITE_BLOCKED_OPERATORS` + `require_write_operator` (`database.py:46,119-126`); `set_context` enforces at `:734`; UI `requireWriteOperator` (`app.js:329-336`).
- **(b)** `check_operator_tree.py:27-38,118-121`; `check_ui_contract.py:140-151`.
- **(c)** HIT.

### 9. Unprotected `power_on` / DP832 30V 3A

- **(a)** OK. `power_on` raises; tests use `power_on_protected` only.
- **(b)** `ate/drivers/check_psu_protect.py:22-60` (not under `check_*.py` but fail-closed).
- **(c)** HIT (driver check).

### 10. Instruments session missing `dmm`

- **(a)** OK. `session.py:35` live open; `:54` SIM `SimResource("DMM")`.
- **(b)** `check_sim_run.py:37-63` exercises SIM DMM; `check_mapped_tests.py:33-49` classifies DMM IDN only -- **no `Instruments.dmm` attribute assert**.
- **(c)** GAP: `check_visa.py` assert `self.dmm` + `simulated().dmm`.

### 11. Combo change auto `applyDb`

- **(a)** OK. Combo listener ends with log-only (`app.js:2440-2444`).
- **(b)** `check_ui_contract.py:184-191`.
- **(c)** HIT.

### 12. False-green checks that only list tests

- **(a)** N/A (process defect). `check_family_load` / `check_mapped_tests` list registry ids; `check_demo_families` + `check_sim_run` run SIM sequences.
- **(b)** Run proof: `check_demo_families.py:49-86`, `check_sim_run.py:159-225`. List-only: `check_family_load.py:201-312`.
- **(c)** GAP: tie `check_family_load` to at least one SIM `run_sequence` smoke (or subprocess `check_demo_families`).

### 13. Slew Cnt=0 stall on simulated scope

- **(a)** OK. `wait_slew_statistics` no-ops on `scope.simulated` (`mso5072.py:201-202`).
- **(b)** `check_sim_run.py:71-75`; `ate/drivers/check_slew_capture_run.py:101-106,135-137`.
- **(c)** HIT.

### 14. `wait_slew` / `VI_ERROR_SYSTEM_ERROR` reopen

- **(a)** OK. `is_visa_poison`, `_reopen_mso_after_visa`, retry loop (`runner.py:836,893-905,961,988-993`).
- **(b)** `ate/drivers/check_slew_capture_run.py:149-163`.
- **(c)** HIT.

## Parent close (same sitting)

Closed GAPS 3, 4, 5, 6, 10:

- `check_sim_run` asserts SIM photo-paste skip + worker must not `or "rs622"`
- `check_open_inventory` rglob `ate/tests` AST `input()` + vendor import
- `check_visa` asserts `simulated().dmm`

Left open: GAP 12 (do not nest `check_demo_families` inside `check_family_load`; run both).

## Verify commands

```
python -m ate.core.check_sim_run
python -m ate.core.check_ui_contract
python -m ate.core.check_session_values
python -m ate.core.check_operator_tree
python -m ate.core.check_add_test
python -m ate.core.check_test_detect
python -m ate.core.check_logic_campaign
python -m ate.core.check_open_inventory
python -m ate.core.check_visa
python -m ate.core.check_family_load
python -m ate.core.check_demo_families
python -m ate.reporting.check_photo_layout
python -m ate.drivers.check_psu_protect
python -m ate.drivers.check_slew_capture_run
```
