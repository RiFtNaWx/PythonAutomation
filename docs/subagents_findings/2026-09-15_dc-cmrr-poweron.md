---
keywords: junior, cmrr, power_on, psrr, mapped, dual-rail, sim-dmm, rs622
main_idea: Mapped CMRR and PowerOn replaced with DC Vcm-step CMRR_dB and MSO rail-to-VOUT delay. SIM dual-rail DMM follows Vin so PSRR/CMRR are not CMOS VOH. SIM 219/219. Not junior-100%.
---

# 2026-09-15 DC CMRR + PowerOn

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_dc-psrr-switch-vth.md. Spawn: skip.

## This sitting

1. SIM DMM: when PSU CH1 and CH2 are matched dual-rail, Vout follows AWG DC plus typ PSRR/CMRR leaks. Logic (CH1 only) stays CMOS high/low.
2. Path B `cmrr`: Vs=5.5, Vcm -0.1 then 4.0, stamp CMRR_dB from dVcm/d(Vout-Vin). Mapped screenshot row removed.
3. Path B `power_on_time`: MSO RRDelay CH1=VCC rail to CH2=VOUT. Stamp POWERON_ns, no invented min/max.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_family_load
python -m ate.core.check_stimulus
python -m ate.core.check_specs_datalog
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM **219/219**. rs622 KEEP now `psrr, cmrr, vohl`. USB DMM/MSO is still the production number.

## Leftover-honest (goal still open)

- AOL/EMIRR still mapped captures. Noise = 0.1-10 Hz Vpp not nV/rtHz. ISC missing
- Analog-switch BW 110 MHz / ISO / XTalk; rON min/max PDF image
- RS0302 empty suite. RS74AUP1G07 no PDF VOH/VOL
- Excel unique VOX Vcc rows; RS0204 Icc/VOH empty/grid
- USB START of every SKU
- Path C `input_off_leakage` unfilled
