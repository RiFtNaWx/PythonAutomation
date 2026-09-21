---
keywords: junior, rs2323, iso, xtalk, seelim, isolation, generator_setup, park_generator_idle, leftover-honest
main_idea: SeeLim goldens keep golden psu_setup/dmm_setup during the test and repo generator_setup always (park_generator_idle). RS2323 Path B iso + xtalk are 1 MHz high-Z, not 50 ohm RF / 110 MHz BW. Not junior-100%.
---

# RS2323 ISO/XTalk + SeeLim path isolate

## SeeLim (RS1G97 / RS1G126)

Cause: `_isolated_folder` used to pop `generator_setup`. Runner `_safe_idle_for_operator` does `from generator_setup import park_generator_idle` while isolation is still active. Golden `generator_setup.py` has no `park_generator_idle`. Pinning *repo* `psu_setup`/`dmm_setup` then broke `query_psu_mode` / `clear_dmm_buffer` and repo OVP 6.05 on 5.5 V `input_threshold`.

Fix in `ate/tests/logic/seelim_dc.py` (do not edit `runner.py`, do not rewrite goldens):

- Prefer `goldens/see_lin/<PART>/` when `current_tests.py` exists.
- Strip golden folder from all of `sys.path`.
- `_NullLog.log_test` (golden `logger=None` crashed).
- `_SIBLINGS` includes golden `psu_setup` + `dmm_setup` (and not `generator_setup`).
- `_ensure_repo_setup()` imports repo `generator_setup` before inserting golden path.

Check: `check_all_parts` SIM 212/212 before xtalk; xtalk adds one RS2323 slot.

## Path B analog switch RF-adjacent

- `iso`: IN1=GND, AWG 1 MHz on NC1, MSO NC/COM, `ISO_dB=20*log10(Vcom/Vnc)`.
- `xtalk`: IN1=IN2=GND, AWG 1 MHz on COM1, MSO COM1/COM2, `XTALK_dB=20*log10(Vcom2/Vcom1)`.
- SIM must not use CHAN2 (G11 GBW sine). Couple `1e-3`.
- Not enabled on RS2227. No invented min/max. MSO5072 is 70 MHz -- do not stamp 110 MHz BW.

## Leftover-honest (goal not complete)

1. Analog-switch **BW 110/550 MHz** still not a body. MSO is 70 MHz.
2. ISO/XTalk are **1 MHz high-Z**, not datasheet 50 ohm RF figures.
3. rON min/max still PDF image.
4. OpAmp **AOL / EMIRR** still mapped screenshots. BUFFER/G11 cannot measure open-loop AOL_dB.
5. **Noise** is 0.1-10 Hz Vpp, not nV/rtHz. **Settling** still photo/cursor. **ISC** not enabled.
6. RS0302 RON 64 mA leftover. No tPLH/tPHL ns body.
7. RS74AUP1G07 no PDF VOH/VOL. RS1G97 VOH/VOL not enabled. RS1G126 TEN/TDIS still manual.
8. Excel: unique VOX Vcc rows only. Never guess A91.
9. USB START of every SKU is not SIM. Path C `input_off_leakage` stays unfilled/not enabled.
10. SeeLim RS2323 UQFN book is a Parameter stub, not a UQFN-probed senior layout.
