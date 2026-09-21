---
keywords: junior, ten, tdis, oe_timing, rs1g126, rs1g125, oe_active, leftover-honest
main_idea: Path B ten/tdis in oe_timing.py follows part yaml oe_active (RS1G126 high RR/FF, RS1G125 /OE low FF/RR). Wrap logic_tests.test_ten is gone. Not junior-100%.
---

PREFLIGHT: PARTIAL
reuse: `docs/subagents_findings/2026-09-15_seelim-pic-honest-catalog.md`, `2026-09-15_seelim-rs1g97-126-goldens.md`, `2026-09-15_rs2227-usb-iso-rs622-aol.md`
spawn: skip

## Closed this sitting

1. `ate/tests/logic/oe_timing.py` Path B `ten` / `tdis`. Stamps `TEN_ns` / `TDIS_ns`. Active-high (RS1G126): A=VCC, 10k pull-down Y, TEN=RRDelay, TDIS=FFDelay. Active-low (RS1G125 /OE): A=0 V, 10k pull-up Y, TEN=FFDelay, TDIS=RRDelay. `power_on_protected`. Continue. No `input()`. Not Ariff wrap. Not RS0204 tsu/th.
2. `wraps.py` no longer registers `ten`/`tdis`. `__init__.py` imports `oe_timing` after `wraps`.
3. RS1G126 `enabled_tests` includes `ten`/`tdis`. RS1G97 still bans them (no OE). Limits have `TEN_ns`/`TDIS_ns` with no invented min/max.
4. Checks: `check_add_test`, `check_family_load`, `check_stimulus`, `check_specs_datalog`, `check_campaign_outline`, `check_sim_run` (126 RR/FF vs 125 FF/RR), `check_all_parts` SIM **218/218**.
5. SeeLim SC70-5 stub workbook gained TEN/TDIS Parameter tabs. JianHong SC70-5 stub already had TEN/TDIS; extra SeeLim original tabs synced. SOT23 Eugene/Lim leftover trees had no xlsx -- Parameter stubs created (not the inventory SC70-5 SKU).

## Leftover-honest (goal not complete)

1. Analog-switch **110/550 MHz BW**. ISO/XTalk/USB ISO are 1 MHz high-Z, not 50 ohm RF. MSO5072 is 70 MHz.
2. rON min/max still PDF image.
3. AOL/EMIRR still mapped if a campaign catalog ticks them. BUFFER/G11 cannot measure open-loop AOL_dB. ISC missing. Settling still photo. Noise is 0.1-10 Hz Vpp not nV/rtHz.
4. RS0302 64 mA RON. RS74AUP1G07 no PDF VOH. SeeLim RS1G97 VOH/VOL not in his tree. Path C `input_off_leakage` unfilled.
5. USB START of every SKU is not SIM. Excel unique VOX rows only. JianHong RS1G126 stub still has leftover Ariff VIH/VOH/CIN tabs plus SeeLim originals.
