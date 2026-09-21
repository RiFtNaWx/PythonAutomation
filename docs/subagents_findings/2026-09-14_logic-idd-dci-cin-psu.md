---
keywords: logic, idd, cin, dci, dmm6500, psu, ch1, rs1g07, conf-curr
main_idea: DMM6500 stayed on DCV because dmm_setup only sent SENS:FUNC. Now :CONF:CURR:DC. RS1G07 IDD uses Eugene CH1+AWG DC. CIN/CPD force CH2/CH3 OFF and AWG high-Z.
---

# 2026-09-14 Logic IDD DCI + CIN PSU

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_logic-ldo-usb-dmm, Eugene RS1G07_test.py, dmm_setup.py. Spawn: skip.

User: Logic IDD not working, DMM not DCI, CIN PSU all wrong.

## Cause

1. Previous USB pass dropped `*RST` and left `:SENS:FUNC "CURR:DC"`. DMM6500 front panel stays DCV unless `:CONF:CURR:DC` runs.
2. RS1G07 `supply_current` was Soo one-shot (CH1 only, no AWG). Golden IDD is PSU CH1 VCC + AWG CH1 DC on Input A + DMM DCI.
3. CIN/CPD programmed CH1 but left leftover CH2/CH3 ON (LDO/OpAmp) and AWG 50 ohm (2x Vpp into CMOS).

## Fix

- `dmm_setup.py`: `*CLS` + `:CONF:CURR:DC 0.01` + golden `SENS:FUNC 'CURR:DC'`. No `*RST`. Restore `dmm_setup_current_continuous`.
- `eugene_cap.py`: CH2/CH3 OFF, CH1=VCC, AWG `LOAD INF`, CIN 3.3 V / vcc+0.2 OVP / 0.2 A OCP. `run_idd` corners 1.65/3.3/5.0/5.5 x Input A 0/5.5, stamps `ICC_uA`.
- `wraps.py`: rs1g07 / rs74aup1g07 `supply_current` dispatches to `run_idd`.

Checks: `check_add_test`, `check_stimulus` (SIM DCI), `check_sim_run` RS1G07 suite, `check_psu_protect`.

Worker was busy on live USB -- do not restart mid-run. Header STOP, then `restart_ate_worker.bat`, Ctrl+F5.
