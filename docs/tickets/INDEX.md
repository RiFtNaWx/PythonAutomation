# Tickets -- scale ledger

**Date:** 2026-09-15  
**Rule:** one wave. Do not unpark A13. A14 Recipe canvas is unparked (PRD-005). Do not scrape en.run-ic.com into `#Test_Database`.  
**How to vibe-code / add a test:** [VIBE_CODE.md](../VIBE_CODE.md). Ship order: [SHIP_NEXT.md](../SHIP_NEXT.md). **PRD-002:** [PRD-002-operator-profile-workflow.md](../prd/PRD-002-operator-profile-workflow.md) (A22 implemented; A23 next on that board). **PRD-003:** [PRD-003-snippet-pointer-trigger.md](../prd/PRD-003-snippet-pointer-trigger.md) (A27-T01/T02/T03 implemented 2026-09-15; leftover A16 `imported_input_off_leakage.py`). Do not fly A27 with A25/A26.

Status words: **closed** = epic/ticket accepted; **implemented** = code in tree (R-0003 may still be pending); **leftover** = honesty gap, not a reopen; **parked** = founder must unpark; **verify** = independent R-0003.

## 1. All filed tickets

| ID | Epic | Ticket file | Status | Leftover (do not fake-close) |
|----|------|-------------|--------|------------------------------|
| A01-T01 | A01 family plugin | A01-T01-family-plugin-load-api.md | closed | -- |
| A01-T02 | A01 left rail | A01-T02-rpc-ui-left-rail.md | closed | -- |
| A02-T01 | A02 logic wraps | A02-T01-logic-testspec-wraps.md | closed-accepted | -- |
| A03 | add-test slot | (no ticket; epic closed) | closed-accepted | Precise realize vs wrap: [VIBE_CODE.md](../VIBE_CODE.md) Path B/C |
| A04-T01 | A04 timing | A04-T01-family-conditions-timing.md | closed-accepted | -- |
| A05-T01 | A05 lab-report sync | A05-T01-lab-report-sync.md | closed-accepted | -- |
| A06-T01 | A06 buffer wraps | A06-T01-la1-buffer-wraps.md | closed-accepted | -- |
| A07-T01 | A07 photo layout | A07-T01-photo-layout-preview.md | closed-accepted | R-0003 2026-09-13; GET /shot live HTTP not this sitting |
| A08-T01 | A08 mapped DMM | A08-T01-mapped-tests-dmm.md | closed-accepted | R-0003 leftover-honest: PSRR/CMRR/AOL still mapped captures |
| A09-T01 | A09 logic yaml | A09-T01-logic-campaign-yaml.md | closed-accepted | R-0003 2026-09-13 |
| A10-T01 | A10 LIM RS2323 | A10-T01-lim-rs2323.md | closed-accepted | R-0003 leftover-honest: rON table still PDF image |
| A11-T01 | A11 RS0204 | A11-T01-rs0204-campaign.md | closed-accepted | R-0003 leftover-honest: Icc/VOH Excel grid unmapped |
| A12-T01 | A12 Ariff wraps | A12-T01-ariff-latest-wraps.md | closed-accepted | R-0003 2026-09-13 |
| A15-T01 | A15 operator folder | A15-T01-operator-folder.md | implemented | migrate file superseded |
| A15-T01b | A15 migrate | A15-T01-operator-folder-migrate.md | implemented (superseded) | -- |
| A15-T02 | A15 category | A15-T02-category-switch.md | implemented | switches-suite file superseded |
| A15-T02b | A15 switches suite | A15-T02-category-switches-suite.md | implemented (superseded) | -- |
| A15-T03 | A15 PSU protect | A15-T03-psu-protect.md | implemented | awg-protect file superseded |
| A15-T03b | A15 PSU/AWG | A15-T03-psu-awg-protect.md | implemented (superseded) | -- |
| A16-T01 | A16 detect/wrap API | A16-T01-detect-wrap-copy.md | implemented | Wrap = scaffold leftover; follow-on A27 pointer+trigger. Do not reopen this ticket |
| A16-T02 | A16 Setup UI | A16-T02-setup-plus-version-session.md | implemented | Copy-from-part parked |
| A17-T01 | A17 tags datalog | A17-T01-tags-datalog.md | implemented | -- |
| A17-T02 | A17 UI contract | A17-T02-tags-ui-contract.md | implemented | -- |
| A17-T03 | A17 auto paste | A17-T03-auto-paste-golden.md | implemented | -- |
| A18 | JSON merge | (epic; no T0x file) | done | -- |
| A19-T01 | A19 session values | A19-T01-session-values.md | implemented | VOX unique Vcc rows only; yaml 2.0/3.3/5.0/5.5 have no VOX row; RS0204 Icc/VOH unmapped |
| A20-T01 | A20 local limits | A20-T01-local-limits.md | implemented | RS2323 rON min/max still a PDF image -- do not invent a table |
| A21-T01 | A21 combo apply | A21-T01-combo-apply-only.md | implemented | -- |
| A22-T01 | A22 assign folders | A22-T01-assign-ensure-unmatched.md | implemented | RPC/core; migrate != MOVE |
| A22-T02 | A22 Setup picker | A22-T02-setup-product-code-picker.md | implemented | Ctrl+F5; person-sku chips |
| A27-T01 | A27 snippet map | A27-T01-snippet-map-scan.md | implemented | vendor AST + located; map SoT |
| A27-T02 | A27 wrap trigger | A27-T02-wrap-trigger-original.md | implemented | no new imported_*.py; leftover scaffold stays |
| A27-T03 | A27 UI source | A27-T03-ui-scan-source.md | implemented | list_tests.source; Ctrl+F5 |
| A14-T01 | A14 recipe shell | A14-T01-recipe-shell.md | implemented | tab + xyflow dist + save/load |
| A14-T02 | A14 palette grep | A14-T02-palette-grep.md | implemented | opcodes + product/user |
| A14-T03 | A14 walker DEMO | A14-T03-walker-demo.md | implemented | recipe_walk + _run_one |

Duplicate ticket filenames (T01 migrate / T02 switches-suite / T03 awg-protect) are **superseded**. Do not re-implement them.

## 2. Epics with no ticket file (or tickets blocked)

| ID | Status | Note |
|----|--------|------|
| A03 | closed-accepted | Slot exists; realize vs customize documented in VIBE_CODE |
| A13 | parked | OneDrive Excel MCP. Founder unpark only |
| A14 | implemented | Recipe canvas + closed interpreter (PRD-005). T01-T03 done 2026-09-15 |
| A18 | done | Living JSON merge |
| A23 | blocked | Forget passphrase. After A22 close (A22 implemented 2026-09-14). Cut tickets next |
| A24 | blocked | Version limits+params overlay. No tickets yet |
| A25 | blocked | Same-family suggest-enable. No tickets yet. Do not fly with A27 |
| A26 | blocked | Named test groups. After A25. No tickets yet. Do not fly with A27 |
| A28 | implemented | Scalable recipe PRD-004: vcc_list, 2^n, rails, who-source. A13 parked; A14 unparked via PRD-005 |

A22-T01/T02 **implemented** 2026-09-14 (`assign_owner_products` + Setup person-sku chips). A27-T01/T02/T03 **implemented** 2026-09-15 (PRD-003 pointer+trigger; do not reopen A16). A28 scalable recipe implementing 2026-09-15. A14 Recipe canvas READY (PRD-005).

## 3. What "solve all" means this sitting

Done 2026-09-13:

1. Ledger -- A07-A12 closed-accepted after independent R-0003.
2. V07 -- [2026-09-13_a07-a12-r0003-verify.md](../subagents_findings/2026-09-13_a07-a12-r0003-verify.md).
3. Add-test -- `python -m ate.core.check_add_test` (AST `input()`, not docstring).
4. DEMO acts C-F -- `python -m ate.core.check_demo_families`.

**Cannot close without new evidence:** RS2323 rON image extract; guessed Excel cells; full Comparator/LDO suites; unpark A13; delete `main.py`. A14 unparked via PRD-005. A27 pointer+trigger is implemented; leftover A16 scaffold file stays.

## 4. Proof commands (ticket layers)

```
python -m ate.reporting.check_photo_layout
python -m ate.core.check_mapped_tests
python -m ate.core.check_logic_campaign
python -m ate.core.check_open_inventory
python -m ate.core.check_family_load
python -m ate.core.check_test_detect
python -m ate.core.check_session_values
python -m ate.core.check_specs_datalog
python -m ate.core.check_ui_contract
python -m ate.core.check_add_test
python -m ate.core.check_demo_families
```
