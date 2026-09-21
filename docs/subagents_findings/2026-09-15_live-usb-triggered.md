---
keywords: live-usb, triggered, visa, psu, awg, dmm, mso, leftover-honest, leftover-13, goal-open, check_live_usb, bench_preflight
main_idea: USB now *IDN PSU+AWG+MSO. DMM still not PnP OK. KEEP walker not triggered. No check_live_usb resume. live_usb_stamps 218/0. Leftover 13 unchanged. Goal OPEN.
---

# Live USB triggered? (2026-09-15)

PREFLIGHT: HIT. Reuse `2026-09-15_live-usb-scale.md`. RPC-only. No second-process PyVISA. No `check_visa`. No NI list_resources from this process.

## Result

- triggered: **no**
- reason: KEEP/DMM scale needs PSU+AWG+DMM. DMM yaml `04698204` skipped (not PnP OK / no *IDN).
- ran: **none** (no `check_live_usb resume`). `check_live_usb.py` still has no `resume` walker (`keep`/`all` only queue).
- worker: 8766 up, `busy=false`, session closed. Did not restart. Did not START.
- live_usb_stamps: **n=218 ok=0**. Header mapping updated to PSU+AWG+MSO. 218 skip rows left as-is (do not re-run).
- leftover 13: **unchanged** (settling SETTLE_VPP_V x3, noise Vpp x3, 10 mA rON x3, 1 MHz iso/xtalk x4).
- goal: **OPEN**

## Live map (one RPC `bench_preflight`, ~7s)

| Kind | Serial | Status |
|------|--------|--------|
| PSU | `USB0::0x1AB1::0x0E11::DP8C274303823::INSTR` | present |
| AWG | `USB0::0x1AB1::0x0646::DG8Q274702441::INSTR` | present |
| MSO | `USB0::0x1AB1::0x0515::MS5A274703490::INSTR` | present (new vs yaml ghost `MS5A281500878`) |
| DMM | `USB0::0x05E6::0x6500::04698204::INSTR` | **MISSING** (skip) |

`session_status.mapping` stays `{}` until `discover`/`open_session`. Did not call `discover` after preflight (no hammer).

## Why no resume

MSO *IDN is not enough. Designed walker stamps KEEP on first DMM-capable unique row. DMM missing -> do not start 218 skips, do not fake KEEP, do not unattended `run_sequence` (pause_hook / PSU). Timing ids could theoretically use MSO later; not this sitting.

## Next (human, Device Manager)

1. USBTMC on Keithley 6500: Status=OK (not Unknown). Yaml try-next `04698204`.
2. Idle worker -> `python -m ate.core.check_live_usb resume` (implement resume first if still missing).
3. Unique `(part_key, test_id)` once. Skip `input_off_leakage`. Skip missing instruments. Leftover 13 stay named.

## Do not

- Second-process PyVISA / `check_visa` while worker owns USB
- Re-run 218 skip rows
- Fake DMM *IDN
- Kill worker if another agent is on sim/inverter
- Close the goal
