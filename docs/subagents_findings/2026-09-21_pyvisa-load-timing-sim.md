---
keywords: pyvisa, visa, open_timeout, LOAD INF, loopback, check_visa, check_sim_run, leftover-honest
main_idea: PyVISA load-timing + SIM control pack EXIT 0. Live isolated *IDN found PSU+AWG+DMM+MSO in 9.97s. SIM session 0.000s, loopback 34/34, check_sim_run all families. Not USB START / not Verify PASS.
---

PREFLIGHT: HIT. Reuse 2026-09-13_pyvisa-session-scale, check_visa, check_stimulus, check_sim_run.

## Ran (EXIT 0)

```
python -m ate.core.check_visa
python -m ate.core.check_stimulus
python -m ate.drivers.check_psu_protect
python -m ate.drivers.check_slew_capture_run
python _tmp_loopback.py
python -m ate.core.check_sim_run
```

Helper: `C:\Users\OoiJianHong\_run_ate_visa_sim.bat` (apostrophe path).

## Proof

| Layer | Result |
|-------|--------|
| SIM session load | 0.000s (no RM, no viOpen hang) |
| loopback_check | 34/34 |
| visa_inventory | 9.97s, USB *IDN PSU DP832 + AWG DG822 Pro + DMM6500 + MSO5072 |
| Timeouts | open_timeout=8000; *IDN open 5000 / query 2000; MSO 20s; others 12s |
| AWG LOAD | `:OUTPn:LOAD INF`; no OUTP3/DCYC/FREQ (-116) |
| PSU | power_on banned; OVP 30 V raises; PROT:STAT ON; ceil 6.0 V |
| DMM | no *RST / NPLC / AZER / AVER / TRAC (-113) |
| check_sim_run | Logic/OpAmp/switch/level/power SIM suites OK |

## Code

- `ate/core/check_visa.py` -- `_sim_load_timing_and_control` + timed `visa_inventory`
- `ate/core/check_stimulus.py` -- LOAD INF + fail-closed error list
- `ate/drivers/check_slew_capture_run.py` -- `reopen_scope` uses `_open_url`

## Leftover-honest

- Isolated *IDN is not USB START. START still needs operator Continue.
- SIM is not Verify PASS.
- `visa_inventory` printed `backend=none` because *IDN runs in a child (parent RM not opened). Mapping still live USB.
- leftover-13 iso/xtalk/ron/settling/noise + UNCONFIRMED scale-wave HOLD.
