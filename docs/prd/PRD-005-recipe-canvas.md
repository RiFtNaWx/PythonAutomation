# PRD-005 - Recipe canvas + closed interpreter (A14 unpark)

**Product:** PythonAutomation ATE (operator console + worker)
**Owner:** founder
**Status:** implementing this wave
**Baseline:** [PRD-001](PRD-001-ate-multi-product-platform.md), [PRD-004](PRD-004-scalable-test-recipe.md). Do **not** reopen A01-A28 as failed. A13 stays parked.
**Repos in scope:** this repo (`PythonAutomation` / origin `jian-hong/Python_Automation_JH`)
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Epic home:** A14 at `docs/epics/EPIC-A14-recipe-canvas.md`. Do **not** open GitHub Issues.
**Parked (inherited):** A13 OneDrive Excel MCP, Monaco, ML trainer, delete `main.py`. Live Comparator / Power / Clock measurement suites stay `live: false` until a Path B wave.

---

## 0. Nearness

Live surface is a new **Recipe** tab (`#page-recipe`) with an xyflow React island on `#recipe-root`. Graph yaml is SoT. A closed-opcode walker (`ate/core/recipe_walk.py`) runs on START/DEMO via one hook in `runner._run_one`. Product/user typeahead greps existing yaml. No second ATE. No `eval` / `exec` / `new Function`.

**Verdict:** unpark A14. BAN unrestricted Python. SKIP live Comparator bodies. Path A HTML5 reorder stays.

---

## 1. Press release

### Drag blocks. Closed opcodes. Same START path.

**Subheading:** Engineers draw sweep / 2^n corners / if_else / instrument actions on a Recipe canvas. Save writes `ate/config/recipes/<id>.yaml`. START walks the graph with the same PSU protect + Continue rules as Path B.

**Problem:** "Scale is 2^n and VCC lists, but defining a new scalable test still means writing Python. Who owns which test and which original file is hard to edit. Comparator class exists in run_ic.yaml but has no recipe surface."

**Solution:** Recipe tab + xyflow island (committed dist, no npm for zip users). Opcode ISA. Relationship panel greps product/user. Comparator stays `live: false` yaml class only.

---

## 2. Success assertion

> **WHEN** the operator saves a recipe graph with id `demo_corners`, **THE SYSTEM SHALL** write `ate/config/recipes/demo_corners.yaml` and register a TestSpec for that family on next `load_family`.
>
> **WHEN** START/DEMO runs that id, **THE SYSTEM SHALL** walk allowlisted opcodes only (`sweep`, `for_corners`, `for_list`, `if_else`, `pause`, `psu_set`, `awg_out`, `dmm_read`, `scope_detect`, `screenshot`, `measure`, `end`) and SHALL refuse unknown opcodes.
>
> **WHEN** `for_corners` has n=2 and levels=[0, 5.5], **THE SYSTEM SHALL** enumerate four corners (00, 01, 10, 11).
>
> **WHEN** product typeahead matches RS358, **THE SYSTEM SHALL** attach that SKU to this operator via `owners.yaml` without scraping en.run-ic.com.
>
> **WHEN** A14 is live, **THE SYSTEM SHALL** keep Path A `#campaign-tests` as HTML5 reorder (not canvas).

---

## 3. Out of scope

- Live Comparator / Power / Clock measurement bodies
- Turing unrestricted Python / JS eval
- Second Excel writer / A13 / `database.py` path rewrite
- Copy Ariff catalog onto Eugene
- npm required for zip / START.bat users

---

## 4. Do not

- Call `input()` in walker (use `pause_hook`)
- Bare `power_on` (use `power_on_protected`)
- Edit `FAMILY_PACKAGES` for Comparator this wave
- Unpark A13
