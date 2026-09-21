---
keywords: see-lim, see-lin, rs1g97, rs1g126, goldens, ingest, test_ioz, test_icc, input, _prompt, ten, tdis, voh, vol, cin, rs2227, rs2323, ariff, eugene
main_idea: Downloads `See Lim Repo` matches in-repo `goldens/see_lin` on all copied text files; only extra is venv. See Lin Repo path is missing (ingest typo). No TEN/TDIS/VOH/VOL/CIN tests in See Lim trees; RS1G126 current tests all use _prompt->input().
---

# See Lim originals vs goldens/see_lin (RS1G97, RS1G126)

Date: 2026-09-15. PREFLIGHT reuse: `2026-09-15_ingest-goldens-original.md`, `2026-09-15_golden-detect-ioz.md`.

## Path spelling

| Path | Exists |
|------|--------|
| `C:\Users\OoiJianHong\Downloads\See Lim Repo` | yes (live originals) |
| `C:\Users\OoiJianHong\Downloads\See Lin Repo` | **no** |
| `goldens/see_lin/RS1G97` | yes |
| `goldens/see_lin/RS1G126` | yes |

`ate/core/ingest_goldens.py` still points at `See Lin Repo`. Re-run ingest will skip unless that path is fixed to `See Lim Repo` or a junction is added.

## File tree diff (skip venv, site-packages, __pycache__)

### RS1G97

| Category | Files |
|----------|-------|
| **Downloads only** | `venv/` (full tree, ~3050 files) |
| **goldens only** | none |
| **Both (16 text files)** | `configurations.py`, `current_tests.py`, `datalog.py`, `dmm_setup.py`, `generator_setup.py`, `install.py`, `instruments.py`, `limits.py`, `main.py`, `psu_setup.py`, `readme.txt`, `scope_setup.py`, `screenshot.py`, `temp_control.py`, `threshold_tests.py`, `utils.py` |

Spot-check: `readme.txt`, `main.py` (279 lines), `current_tests.py` (677 lines), `threshold_tests.py` opening blocks are **byte-identical** between Downloads and goldens. No content diffs found on sampled pairs.

### RS1G126

| Category | Files |
|----------|-------|
| **Downloads only** | `venv/` (~3050 files) |
| **goldens only** | none |
| **Both (14 text files)** | same as RS1G97 except **no** `screenshot.py`, `temp_control.py` |

Spot-check: `main.py`, `current_tests.py` (503 lines), `threshold_tests.py` match goldens.

**Conclusion:** `goldens/see_lin` is a clean copy of the SKU folders minus `venv`. Refresh ingest needs the correct Downloads path.

---

## `def test_*` inventory (Downloads See Lim Repo)

`input()` / `_prompt`: `_prompt` is a helper that calls `input()` for wiring pauses. Detect treats both as blocking for Path C wrap.

### RS1G97

| Function | file:line | input() | _prompt |
|----------|-----------|---------|---------|
| `test_icc` | `current_tests.py:343` | no | **yes** (once before 8-state sweep) |
| `test_delta_icc` | `current_tests.py:438` | no | **yes** (once before 6-state sweep) |
| `test_ii` | `current_tests.py:567` | no | **yes** (per pin A/B/C before sweep) |
| `test_input_threshold` | `threshold_tests.py:241` | **yes** (via `_print_wiring` at line 99) | no |

Goldens line numbers match INDEX.md / downloads (same files).

`main.py` REGISTERED_TESTS comment says current_tests disabled (threshold-only default); bodies still present in tree.

### RS1G126

| Function | file:line | input() | _prompt |
|----------|-----------|---------|---------|
| `test_ioff` | `current_tests.py:141` | no | **yes** (3 sub-conditions) |
| `test_ioz` | `current_tests.py:218` | no | **yes** (1 sub-condition) |
| `test_icc` | `current_tests.py:275` | no | **yes** (4 OE/A states) |
| `test_ii` | `current_tests.py:349` | no | **yes** (4 OE/A states) |
| `test_delta_icc` | `current_tests.py:428` | no | **yes** (2 sub-conditions) |
| `test_input_threshold` | `threshold_tests.py:174` | no | no |

`main.py` also has `input()` for test menu (line 68) -- not a `test_*`.

---

## TEN / TDIS / VOH / VOL / CIN as Python tests (See Lim SKUs)

| Test id | RS1G97 | RS1G126 |
|---------|--------|---------|
| TEN | **no** | **no** |
| TDIS | **no** | **no** |
| VOH | **no** | **no** |
| VOL | **no** | **no** |
| CIN | **no** | **no** |

No `def test_ten`, `test_tdis`, `test_voh`, `test_vol`, or `test_cin` under either SKU tree (non-venv `.py` only). These parts use current + threshold suites only.

---

## RS2227 / RS2323 in See Lim Repo

| SKU | Hits |
|-----|------|
| RS2227 | **none** |
| RS2323 | comment only in `RS1G126/current_tests.py` line 4-15 (modelled on rs2323_tests.py; not a test body) |

No RS2227/RS2323 folders or test modules in See Lim Repo.

---

## Ariff Repo -- logic `test_*` names

Source: `Downloads/Ariff Repo/LabAutomation test/LabAutomation_v1 - Copy/logic_tests.py` (skip venv).

**Active (uncommented):**

- `test_tp`
- `test_tidle`
- `test_tdis`
- `test_supply_current`
- `test_delta_supply_current`
- `test_off_current`
- `test_input_thresholds`
- `test_ioff_leakage`
- `test_input_leakage_sweep`
- `test_vih_vil`
- `test_input_threshold`
- `test_voh`
- `test_vol`

**Commented out in same file:** `test_ten`, `test_output_voltage`, `test_cap_load`, and many switch/LIM stubs.

`main.py` also defines `test_generator_procedures` (not logic timing).

---

## Eugene Repo -- RS1G07 / RS1G14 / RS622 `test_*`

Source: `Downloads/Eugene Repo/LabAutomation-1/Eugene/`

### RS1G07 (`RS1G07/RS1G07_test.py`)

- `test_supply_current`
- `test_delta_supply_current`
- `test_input_leakage_sweep`
- `test_input_off_leakage`
- `test_cpd`
- `test_cin`

### RS1G14 (`RS1G14/RS1G14_test.py`)

- `test_pvt`
- `test_nvt`
- `test_supply_current`
- `test_delta_supply_current`
- `test_input_leakage_sweep`
- `test_input_off_leakage`
- `test_cpd`
- `test_cin`

Duplicate copy also at `Eugene/RS1G14_test.py` plus `test_ioz` there.

### RS622 (`RS622/opa_tests.py`)

- `test_parameter` (helper config, not a measurement)
- `test_gbw`
- `test_sr`
- `test_settlingTime`
- `test_SSR`
- `test_LSR`
- `test_ORT`
- `test_NPR`
- `test_powerONtime`
- `test_flicker_noise`
- `test_noise_bucket`

---

## Wrap / Path B notes

- RS1G126 `test_ioz` / `test_ioff` / ICC family: **Path C blocked** (`_prompt` -> `input()`). Path B `ioz` already in `ate/tests/logic/ariff_dc.py` per prior finding.
- RS1G97 `test_input_threshold`: **Path C blocked** (`input()` in `_print_wiring`); use Path B `input_thresholds` / `vih_vil` pattern from Ariff/Lim.
- Re-ingest: fix `ingest_goldens.py` source path to `See Lim Repo` before `python -m ate.core.ingest_goldens`.
