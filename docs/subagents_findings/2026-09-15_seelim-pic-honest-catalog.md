---
keywords: seelim, pic, rs2227, rs1g97, rs1g126, honest-catalog, goldens, see-lim, input-threshold, vih_vil, snippet, ariff, jianhong, venv-prune
main_idea: RS2227 is SeeLim Wuxi completed (nobody holding). RS1G97/RS1G126 PIC SeeLim with only his original test_* (no Ariff VIH/VOH dump). Scan prunes venv, author-scopes goldens, Load/Save edits Downloads originals.
---

# SeeLim PIC + honest catalogs (2026-09-15)

PREFLIGHT: HIT reuse `2026-09-15_seelim-rs1g97-126-goldens.md`, `2026-09-15_seelim-honest-catalog-checks.md`.

## Why Ariff showed up

`check_add_test` used to force `rs1g97`/`rs1g126` to start with Ariff `vih_vil, voh_load, vol_load`. Scan aliases mapped SeeLim `test_icc` -> `supply_current`. Empty PIC made 1G97/126 look unowned. JianHong default_part was RS2227.

## Honest map (from See Lim Repo, not invented)

| SKU | PIC | Status | Enabled TestSpec ids | Not enabled |
|-----|-----|--------|----------------------|-------------|
| RS2227 | seelim | Completed (nobody holding) | USB Path B already in `lim/rs2227.py` | RS2323 COM/NO ids |
| RS1G97 | seelim | TBD pickup | `icc`, `delta_icc`, `ii`, `input_threshold` | VOH/VOL (unwritten), Ariff vih_vil, cin |
| RS1G126 | seelim | TBD pickup | `ioff`, `ioz`, `icc`, `ii`, `delta_icc`, `input_threshold` | TEN/TDIS (manual, no Python) |

`input_threshold` is VIH/VIL. UI hides `vih_vil` duplicates.

START calls original `goldens/see_lin` or `Downloads/See Lim Repo` via `ate/tests/logic/seelim_dc.py`. `input()`/`_prompt` -> Continue. Wrap of dirty goldens still raises.

## Scan

- `os.walk` prunes `venv`/`site-packages` (rglob was walking pandas tests).
- Author filter skips untagged LabAutomation dumps.
- Located rows prefer Downloads originals over `seelim_dc.py` wrappers.
