---
keywords: sim, chan2, oe-dc, fmax, rtime, cio, rs0204, ten, tdis, leftover-honest
main_idea: SIM MSO CHAN2 no longer follows AWG CH2 DC (OE). RS0204 fmax is 20 Mbps DUT Y, tr/tf is MSO 5 ns, cpd stamps pin CIO_A_pF. tsu/th stay TEN_ns/TDIS_ns. Leftover 13 unchanged. Goal OPEN.
---

PREFLIGHT: PARTIAL
reuse: `docs/subagents_findings/2026-09-15_sim-stamp-must-ids.md`, `2026-09-15_seelim-nan-ch3.md`, `2026-09-15_oe-timing-ten-tdis.md`, `2026-09-15_physics-scale-proof.md`
spawn: skip

# SIM CHAN2 OE-DC + RS0204 Cio (2026-09-15)

## Closed this sitting

1. `ate/instruments/sim.py`: AWG CH2 DC is OE. USB MSO CHAN2 is DUT Y/B. Do not bind CHAN2 to OE DC VPP=0. Translator B VPP follows VCCB. RTime/FTime = 0.35/70e6 (MSO5072 ceiling), not 0.12 s dummy.
2. RS0204 `fmax` FMAX_Mbps 0 -> 20 (AWG sweep ceiling 20 MHz, not PDF 50 Mbps). `tr`/`tf` 1.2e8 ns -> 5.0 ns.
3. `eugene_cap.run_cpd` dispatches RS0204 pin Cio. `__all__` reload of eugene_cap after rs0204 had been hiding `_run_cpd`. Stamp `CIO_A_pF=5.0` (DMM CAP), not I=CVf `CPD_pF`.
4. Stamp gate: `MUST_STAMP_PART (rs0204,cpd)=CIO_A_pF`. FMAX_Mbps<=0 fails. TR/TF > 1e5 ns fails (the 0.12 s dummy). `check_sim_run` asserts CHAN2 OE-DC VPP~VCCB and RTime ns-class.
5. RS0204 `tsu`/`th` keep stamping `TEN_ns`/`TDIS_ns` (MSO OE delay). Do not invent `TSU_ns` from CMOS OE.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM **218/218**. physics REALIZED=205 LEFTOVER=13. `sim_stamps.json` n=218 ok=218.

File stamps: rs0204 cpd `CIO_A_pF=5.0`, fmax `FMAX_Mbps=20.0`, tr/tf `5.0` ns, tsu `TEN_ns=50`, th `TDIS_ns=50`.

Worker idle-restarted on 8766 after sim.py / eugene_cap / rs0204. ping ok.

## Leftover-honest (not leftover 13)

- SIM LIR_mV ~1600: no LDO model; DMM follows VIN.
- LM358 SR_Vus ~5.55 vs typ 0.5: SIM 1-pole slew.
- all-GBW GBW_MHz=7.006 SIM G11 1-pole.
- rs0204 tsu/th workbook names; USB meaning is ten/tdis (OE delay).
- rs0204 FMAX_Mbps=20 AWG cap, not datasheet 50 Mbps.
- rs0204 TR/TF=5 ns is MSO 70 MHz ceiling, not DUT typ 6.6 ns.

## Leftover 13 (must stay; do not reclassify)

iso/xtalk 1 MHz not 110 MHz; usb_iso/usb_xtalk 1 MHz not 550 MHz; ron/usb_ron/i2c_ron 10 mA; settling SETTLE_VPP_V not 0.1% SETTLE_us; noise Vpp not nV/rtHz.

## Do not

- Invent TSU_ns from CMOS OE.
- Fake LDO dropout, datasheet GBW, 0.5 V/us slew, 50 Mbps fmax, or 6.6 ns tr.
- Reclassify leftover 13.
- Hammer NI-VISA / second USB session. live_usb_stamps.json stays ok=0 (DMM+MSO not PnP).

## Goal

OPEN.
