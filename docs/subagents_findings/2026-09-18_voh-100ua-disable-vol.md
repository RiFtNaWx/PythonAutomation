---
keywords: [rs1gt34, voh_load, vol_load, 100uA, dmm-113, visa, cha-duplicate, continue]
main_idea: 100 uA VOH/VOL is off until the current source can sink it (Tests checkbox). Skip full PSU-off between corners. DMM CONF once then READ. Hide dut_change CHA row. VOL uses the same Path B wait.
---

# VOH 100 uA disable + VOL ready

## Why last START failed

- `SPEC FAIL VOH_5p5V_100uA=5.396927 min=5.4` -- DP832 + 10 ohm cannot source 100 uA. Y stayed at unloaded VCC. Physics 8/24/32 mA was 10/10; STS still FAIL because yaml 100 uA min 5.4.
- That FAIL flipped `step.success`, so WAIT said `DUT #1 CHA FAILED -- Continue to next unit`. Continue was the DUT gate, not a VOH bug.
- `psu off: VI_ERROR_SYSTEM_ERROR` then `reopen_bench ... RSRC_NFOUND` -- `_run_voh_load` called full `power_off` after every corner (10x), then runner SAFE IDLE `power_off` again on the WAIT. Handle died.
- DMM -113 -- `_avg_voltage` sent `:SENS:VOLT:DC:RANG:AUTO ON` on every sample. This DMM6500 treats that header as undefined. `:CONF:VOLT:DC` + `:READ?` is enough.
- Two CHA rows -- timeline `dut_change` label already has CHA, UI also appended `[CHA]`, then the test row did it again.

## Sweep (what it actually is)

Not a dense VCC start/stop. Datasheet corners only: 100 uA (now skipped) then 8/24/32 mA at 2.0 / 3.3 / 4.5 / 5.0 / 5.5. Tick `Include 100 uA` on Tests Parameters after resolder. `load_r_ohm` default 10.

## VOL

Same Path B `vol_load`: Continue wait, 10 ohm IOL table, no 100 uA unless `vol_100ua`, CONF DMM once, no full power_off between corners.
