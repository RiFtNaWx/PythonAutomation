---
keywords: logic, awg, mso, ch1, ch2, logic_inputs, 2^n, corners, ariff_dc, cmos_prop, oe_timing, clk_q, pulse_width, demo_corners, cha, run_prefs, sim, chan2-oe-dc
main_idea: 2^n is AWG input-corner enumeration (itertools.product), never extra MSO probes. DG822 has 2 AWG outs; MSO5072 has 2 analog CH. Timing tests always MSO CH1=stimulus ref, CH2=DUT output. Ariff DC drives corners on AWG CH1/CH2 with pause_hook rewire for n>2. CHA/CHB is DUT socket selection (run_prefs), unrelated to 2^n.
---

PREFLIGHT: PARTIAL. Reuse `2026-09-15_scalable-test-recipe.md`, `2026-09-15_inverter-y-polarity.md`, `2026-09-15_sim-chan2-oe-dc-fmax.md`, `ate/tests/logic/ariff_dc.py`, `ate/tests/logic/cmos_prop.py`, `ate/core/recipe_walk.py`.

## Three channel axes (do not mix)

| Axis | What it is | Where | Scales with logic_inputs n? |
|------|------------|-------|------------------------------|
| **AWG CH1/CH2** | Rigol DG822 stimulus outputs | `generator_setup.setup_dc` / `setup_square` | Corners yes (2^n combos); physical channels no (always 2) |
| **MSO CH1/CH2** | MSO5072 scope probe inputs | `scope_setup.measure_delay` / `measure_single` | **Never** -- always 2 probes |
| **CHA/CHB** | DUT socket half (operator run_prefs) | `RunParams.channel`, `probe_channels` in `_manifest/run_prefs.yaml` | **Never** -- Logic tests set `dual_channel=False` |

`specs.py:138` documents CHA..CHH as DUT probe positions, not PSU CH1.

## What 2^n means

- `logic_inputs` = n input **pins** on the DUT whose levels are swept.
- `_input_corners(n, levels)` = `itertools.product(levels, repeat=n)` -> `len(levels)^n` tuples (`ariff_dc.py:173-177`).
- Example: n=2, levels=[0, 5.5] -> 4 corners: (0,0), (0,5.5), (5.5,0), (5.5,5.5).
- n=3 -> 8 corners; only first two tuple entries map to AWG CH1/CH2; IN3+ need bench rewire (`ariff_dc.py:214-225`, `recipe_walk.py:184-187`).
- **Not** MSO channel count. No Logic test allocates CHAN3..CHANn on the scope.

Hardware ceiling: `generator_setup.py:2-8` `_AWG_CHS = (1, 2)`; `ariff_dc.py:24-25` `_AWG_DRIVE_CH = 2`.

---

## Per-family map

### 1. DC Ariff (`ate/tests/logic/ariff_dc.py`)

| Test id | Instruments | AWG | MSO | PSU | 2^n / logic_inputs |
|---------|-------------|-----|-----|-----|-------------------|
| `delta_supply_current` | PSU, AWG, DMM | CH1/CH2 alternate high (`:280-291`); skip CH2 if n=1 (`:282-283`) | none | CH1=VCC | n from `_logic_inputs` (`:262`); not full 2^n -- alternates one-hot |
| `off_current` | PSU, AWG, DMM | CH1=A, CH2=B DC (`:352-353`) | none | CH1=0, CH2=Y force | fixed 2^3=8 combos A,B,Y (`:337-346`) -- **not** wired to `logic_inputs` |
| `input_thresholds` | PSU, AWG, DMM | CH1=VIN sweep (`:399`) | none | CH1=VCC | n unused |
| `ioff_leakage` | PSU, AWG, DMM | CH1=A, CH2=B (`:464-465`) | none | CH1=VCC, CH2=Y | fixed 8 combos (`:447-456`) |
| `input_leakage_sweep` | PSU, AWG, DMM | `_drive_corner` -> CH1/CH2 (`:523-525`) | none | CH1=VCC sweep | **2^n** via `_input_corners` (`:516-522`) |
| `supply_current_sweep` | PSU, AWG, DMM | same | none | CH1=VCC sweep | **2^n** (`:578-587`) |
| `vih_vil` | PSU, AWG, DMM | CH1=sweep pin; CH2=other input high if n>1 (`:656-657`) | none | CH1=VCC | n gates CH2 (`:640`) |
| `voh_load` / `vol_load` | PSU, AWG, DMM | `_drive_inputs` both to same level (`:764`, `:838`) | none | CH1=VCC, CH2=Vref load, CH3=V+ | n for B strap only |
| `ioz` | PSU, DMM | CH1=A=0 optional (`:925`) | none | CH1=VCC, CH2=Y, CH3=OE | n unused |

All Ariff DC specs: `dual_channel=False` (`:960`), `required_instruments` exclude MSO (`:966-1034`). Runner skips MSO park/recover for these (`check_walk_order.py:268-273`).

**`_logic_inputs`** (`:149-160`): overlay `params.logic_inputs` -> part yaml -> default 2; cap 8.

**`_drive_corner`** (`:203-225`): AWG CH1=corner[0], CH2=corner[1]; if n>2, `pause_hook` lists IN3..INn for manual wire.

**`_drive_inputs`** (`:191-200`): `setup_dc(gen, 1, a_v)`; if n>1 also `setup_dc(gen, 2, b_v)`.

### 2. CMOS tPD (`ate/tests/logic/cmos_prop.py` via `wraps.py` ids `tp`, `tidle`)

| Field | Value |
|-------|-------|
| Instruments | MSO, PSU, AWG (`cmos_prop.py:50-53`) |
| AWG CH1 | A square 400 kHz (tp) or 100 kHz (tidle) (`:69`) |
| AWG CH2 | AND: DC VCC (`:64-65`); OR: DC GND (`:67-68`); else off/unused |
| MSO | CH1=A, CH2=Y; `measure_delay(item, 1, 2)` (`:70-78`) |
| Inverter RS1G14 | RFDelay/FRDelay instead of FF/RR (`:73-76`) |
| 2^n | **none** -- fixed strap per part family |
| pause_hook | `_wire(pk)` documents bench (`:23-42`, `:48`) |

`check_add_test.py:620-621` blocks reverse-driving CH2 square (legacy level-shifter bug).

### 3. OE timing (`ate/tests/logic/oe_timing.py` ids `ten`, `tdis`)

| Mode | AWG | MSO | measure_delay |
|------|-----|-----|---------------|
| 3-state (RS1G125/126) | CH1=A DC (`:141`); CH2=OE square (`:142`) | CH1=OE, CH2=Y (`:111-117` pause text) | `(item, 1, 2)` (`:146`) |
| RS29511 hot-swap | CH1=EN square only (`_measure_ns` `:52`) | CH1=EN, CH2=READY (`:73-75`) | `(item, 1, 2)` (`:56`) |

2^n: none. `dual_channel=False` (`:187`, `:200`).

### 4. clk_q (`ate/tests/logic/clk_q.py`)

| Field | Value |
|-------|-------|
| Instruments | MSO, PSU, AWG (`:26-29`) |
| AWG CH1 | CLK square (`:40`) |
| AWG CH2 | D or A = VCC DC (`:39`, `:16-17` rs164) |
| MSO | CH1=CLK, CH2=Q/Q0 (`:16-22` pause; `:44-45` measure) |
| 2^n | none |

### 5. pulse_width (`ate/tests/logic/pulse_width.py`)

| Field | Value |
|-------|-------|
| Instruments | MSO, PSU, AWG (`:18-21`) |
| AWG CH1 | B trigger pulse (`:32`) |
| MSO | **CH2 only** -- Q (`:14-15`, `:34-35` `measure_single(..., 2)`) |
| 2^n | none |

### 6. Recipe `demo_corners` (`ate/config/recipes/demo_corners.yaml`)

| Field | Value |
|-------|-------|
| TestSpec instruments | PSU, DMM only (`recipe_walk.py:415`) |
| Graph | `for_list` VCC x `for_corners` n=2 x `dmm_read` CORNER_V |
| AWG nodes | **none** in yaml -- corners exist in ctx only |
| MSO | **none** |
| 2^n | 2 VCC x 4 corners = 8 DMM readings (`check_recipe.py:61-63`) |

`for_corners` walker (`recipe_walk.py:178-194`): product of levels^n; pause if n>2 before body.

`awg_out` opcode (`:256-278`): maps `corner[i]` to AWG ch; `ch>2` -> pause_hook; uses `instr.awg` (**bug**: session has `instr.gen` only).

---

## generator_setup.py channel contract

- `setup_dc(gen, ch, volts)` -> `:SOUR{ch}:APPL:DC` + `:OUTP{ch} ON` (`:132-144`).
- `setup_square(gen, ch, ...)` -> `:SOUR{ch}:APPL:SQU` (`:18-26`).
- `stop_output(gen)` -> CH1 and CH2 OFF only (`:57-60`).
- Docstring: DG822 Pro 2-channel (`:2-4`). CH3/4 SCPI -> Error 116.

## scope_setup.py channel contract

- `measure_delay(scope, item, ch1, ch2)` -> `CHAN{ch1},CHAN{ch2}` (`scope_setup.py:15-21`).
- `measure_single(scope, item, ch)` -> `CHAN{ch}` (`:23-29`).
- `set_threshold(scope, ch)` per channel (`:40-44`).
- All Logic timing bodies pass literal `1` and `2` -- never `logic_inputs`.

## DUT CHA/CHB (run_prefs) vs MSO

- Setup **Channel A/B** ticks -> `_manifest/run_prefs.yaml` `probe_channels`.
- `RunParams.channel` default `CHA` (`runner.py:76`).
- Logic TestSpecs: `dual_channel=False` -> runner uses `channels[0]` only, skips CHB pass (`runner.py:635-636`, `794-804`).
- CHA/CHB = which DUT socket half; **not** AWG CH1/CH2 and **not** 2^n corners.

---

## Where code wrongly treats n-input as extra MSO channels

**Production Path B bodies: no Logic test scales MSO with logic_inputs.** Grep shows no `logic_inputs` in any `cmos_prop`, `oe_timing`, `clk_q`, or `pulse_width` source.

Actual confusion / bugs:

1. **Operator/UI semantics** -- Parameters label "Inputs n (2^n)" (`app.js:3933`) without "MSO stays 2 probes". Note at `:3949` says AWG 2 CH but easy to misread as scope inputs.

2. **SIM MSO CHAN2 follows AWG CH2 when it should be DUT Y** -- partially fixed for CH2=DC + CH1 toggling (`sim.py:156-163` `_ch2_oe_dc`; `check_add_test.py:285-286`). Still wrong pattern for **oe_timing**: AWG CH1=DC, CH2=OE square -- `_scope_item` line `:196-197` binds CHAN2 to AWG CH2 (OE), not DUT Y, for non-DELAY items. USB bench wiring (MSO CH2 on Y) is correct; SIM can mislead.

3. **cmos_prop AND strap** -- AWG CH2=DC VCC, CH1 square: `_ch2_oe_dc` true -> SIM treats CHAN2 as Y for PWID (`:220-222`). DELAY returns fixed 50 ns (`:207-216`) regardless of ch -- OK for stamp checks.

4. **`recipe_walk.awg_out` uses `instr.awg`** (`recipe_walk.py:268-273`) but `Instruments` exposes `.gen` (`session.py:35`). AWG recipe steps silently skip on live bench until fixed to `getattr(instr, "gen", None) or getattr(instr, "awg", None)`.

5. **`off_current` / `ioff_leakage` hardcoded 8 combos** (`ariff_dc.py:337-346`, `:447-456`) -- 2^3 for pins A,B,Y via PSU+AWG, not `logic_inputs`. Separate from scalable recipe; does not touch MSO.

6. **rs1g97 `logic_inputs: 3`** (`parts/rs1g97.yaml:19`) -- only affects Ariff-style corner math if those tests run; SeeLim enabled tests are `icc`, `delta_icc`, `ii`, `input_threshold` (not `input_leakage_sweep`). No MSO tests on that SKU.

---

## Concrete fix (smallest)

### Already correct (keep)

- `ariff_dc._AWG_DRIVE_CH = 2`, `_drive_corner` pause_hook for n>2 (`ariff_dc.py:24-25`, `:214-225`).
- All Logic timing tests: MSO `measure_delay(..., 1, 2)` or `measure_single(..., 2)` with pause_hook wiring text.
- `dual_channel=False` on all Logic TestSpecs -> no CHA/CHB doubling for MSO tests.
- `recipe_walk.for_corners` pause when n>2 (`recipe_walk.py:184-187`).

### Minimal patches

1. **`recipe_walk.py` `awg_out`** -- use `gen = getattr(instr, "gen", None) or getattr(instr, "awg", None)` before `setup_dc`.

2. **`app.js` Parameters hint** -- change title/note to: `2^n = AWG input corners only. MSO always CH1=stimulus CH2=output (2 probes).`

3. **`sim.py` `_scope_item`** -- add symmetric guard for oe_timing (CH1=DC, CH2=SQU): when measuring CHAN2 and pattern is "control on AWG CH2, DUT Y on probe CH2", return DUT Y model (delay/PWID from CH1 edge), not AWG CH2 waveform. Mirror `_ch2_oe_dc` with `_ch1_dc_ch2_square_oe` for TEN/TDIS/cmos cases.

4. **Do not** add `logic_inputs` to any MSO test. Do not add `measure_delay(..., 1, n)` or enable CHAN3+.

5. **Optional doc** -- one line in `stimulus.py` `supply_current_sweep` / `input_leakage_sweep` detail: "2^n AWG corners; MSO not used."

### Do not

- Scale MSO channels with n.
- Map corner index i to MSO CH(i+1).
- Edit `runner.py` channel gate for this.
- Restart worker for doc-only; restart after `sim.py` / `recipe_walk.py` if changed.

---

## Quick reference table

| Family | MSO? | AWG CH1 | AWG CH2 | MSO CH1 | MSO CH2 | 2^n |
|--------|------|---------|---------|---------|---------|-----|
| Ariff DC | No | IN1 / A | IN2 / B | -- | -- | Yes (leakage/IDD sweeps) |
| CMOS tp/tidle | Yes | A sq | B DC strap | A | Y | No |
| OE ten/tdis | Yes | A DC or EN sq | OE sq or -- | OE/EN | Y/READY | No |
| clk_q | Yes | CLK sq | D/A DC | CLK | Q | No |
| pulse_width | Yes | B pulse | -- | (unused) | Q | No |
| demo_corners | No | (recipe: none) | -- | -- | -- | Yes (DMM only) |
