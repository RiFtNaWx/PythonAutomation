# PRD-004 - Scalable test recipe (2^n corners, VCC lists, rails)

**Product:** PythonAutomation ATE (operator console + worker)
**Owner:** founder
**Status:** implementing this wave
**Baseline:** [PRD-001](PRD-001-ate-multi-product-platform.md), [PRD-002](PRD-002-operator-profile-workflow.md), [PRD-003](PRD-003-snippet-pointer-trigger.md). Do **not** reopen A01-A27 as failed. A16 leftover scaffold stays honesty.
**Repos in scope:** this repo (`PythonAutomation` / origin `jian-hong/Python_Automation_JH`)
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Epic home:** A28 at `docs/epics/EPIC-A28-scalable-test-recipe.md`. Do **not** open GitHub Issues.
**Parked (inherited):** A13 OneDrive Excel MCP, A14 xyflow, no-code wizard that writes Python, Monaco, ML trainer, delete `main.py`. Comparator / Power / Clock stay `live: false` until a real suite exists.

---

## 0. Nearness

Live surface is Setup Test program **Parameters + Write** and Results `#panel-progress-board`. Recipe is yaml data on this Version (`_manifest/test_params.yaml`) and shared part yaml. Physics stays one Path B `TestSpec` id. Do not invent a second ATE or a drag-drop if/else canvas.

**Verdict:** extend-live. SKIP xyflow. BAN wizard-Python, scrape RUN-IC, mix `voh` with `voh_load`.

---

## 1. Press release

### One recipe table. Scale corners and rails. Same Path B body.

**Subheading:** Characterization engineers edit VCC lists, input count (2^n), and single/dual PSU digits on the existing Test program row. START applies them via `RunParams.overlay_for`. Different VOL algorithms stay different TestSpec ids.

**Problem:** "Sweep start/stop/step cannot add 3.5 V next to 1.65/3.3. Dual-input AND needs four corners; buffers need two. `_logic_inputs` caps at 2. Dual vs single supply digits are not visible on the Parameters row. Who owns which original file:line is hard to see."

**Solution:** Recipe keys (`vcc_list`, `logic_inputs`, `levels`, `rails`) in test_params + part yaml. Uncap n (AWG hardware ceiling 2 channels with Continue rewire for n>2). Parameters UI fields. Results who-has-what table (operator x SKU x test id x source). Path B still runs instruments.

---

## 2. Success assertion

> **WHEN** this Version writes `vcc_list: [1.65, 3.3, 3.5]` for a sweep test, **THE SYSTEM SHALL** use that list in `resolved_vcc_sweep` (not only start/stop/step).
>
> **WHEN** `logic_inputs` is 2 and levels are `[0, high]`, **THE SYSTEM SHALL** drive four corners (00, 01, 10, 11). **WHEN** n is 1, **THE SYSTEM SHALL** drive two corners.
>
> **WHEN** Parameters shows rails mode single/dual and PSU CH volts, **Write SHALL** persist `rails` on this Version only.
>
> **WHEN** Results who-has-what loads, **THE SYSTEM SHALL** list operator, SKU, enabled test id, and `source file:line` without rewriting `#Test_Database` trees.

---

## 3. Out of scope

- A14 xyflow / drag-drop if/else/for canvas
- Wizard that authors Python bodies
- Comparator / Power / Clock measurement suites (`live: false`)
- Copy Ariff catalog onto Eugene; mix RS0204 `voh`/`vol` with Ariff `voh_load`/`vol_load`
- Edit `FAMILY_PACKAGES` by hand; scrape en.run-ic.com; A13 Graph; `input()` in TestSpec.run
- Pretending DG822 has more than 2 independent DC channels without mux/rewire

---

## 4. Recipe keys

| Key | Meaning | Wins |
|-----|---------|------|
| `vcc_list` | Explicit VCC points e.g. `[1.65, 3.3, 3.5]` | this Version test_params over part yaml over start/stop/step |
| `logic_inputs` | n inputs; corners = product(levels, repeat=n) | overlay / part yaml |
| `levels` | e.g. `[0, 5.5]` or high follows VCC | overlay / part yaml |
| `rails.mode` | `single` \| `dual` | this Version |
| `rails.psu` | `[{ch, name, volts}]` display digits | this Version |

Named scenario blocks (`normal`, `else_connection`, `dual_input`) may appear in yaml as documentation labels; they are **not** a Turing interpreter.

Hardware ceiling: DG822 has 2 AWG channels. n>2 shows the corner table and uses `pause_hook` to rewire (or later mux).

---

## 5. Do not

- Build a second ATE / second runner stack
- Hardcode test lists in `app.js`
- Rewrite `database.py` path shape
- Unpark A13/A14
