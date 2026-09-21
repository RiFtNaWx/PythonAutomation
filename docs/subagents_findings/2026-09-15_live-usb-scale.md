---
keywords: junior, live-usb, visa, psu, awg, dmm, mso, leftover-honest, check_live_usb, visa_known
main_idea: Live USB *IDN this sitting is PSU+AWG only. DMM and MSO yaml serials skipped (not PnP OK). Cannot stamp KEEP/MSO rows until DMM/MSO *IDN. Leftover 13 unchanged. Goal stays open.
---

# Live USB scale (2026-09-15)

Worker idle on 8766. `bench_preflight` + `discover` (not SIM).

## Live map (first *IDN this sitting)

- PSU `USB0::0x1AB1::0x0E11::DP8C274303823::INSTR`
- AWG `USB0::0x1AB1::0x0646::DG8Q274702441::INSTR`
- DMM / MSO skipped (not PnP OK). Later re-preflight saw PSU/AWG skip too (busy / Unknown after probes). Do not hammer discover.

`visa_known.yaml` PSU/AWG updated to the live serials. DMM/MSO kept as try-next.

218 unique rows in `live_usb_stamps.json`: KEEP missing DMM, MSO ids missing MSO, leftover 13 named. 0 live stamps. Do not repeat those skips until DMM/MSO *IDN.

`ate/config/visa_known.yaml` now points PSU/AWG at the live serials. DMM/MSO kept as try-next.

## Walker

`python -m ate.core.check_live_usb preflight|keep|all`

- RPC only (no second VISA).
- Unique `(part_key, test_id)` once. Resume `live_usb_stamps.json`.
- Skip `input_off_leakage`. Skip tests whose required instruments are not in the live map (named, not a fake PASS).
- Leftover 13 still leftover (iso/xtalk 1 MHz, 10 mA rON, SETTLE_VPP_V, noise Vpp).

## Do not

- Fake DMM/MSO *IDN.
- Re-run SIM 218 to stand in for USB.
- Kill worker if busy.

## Proof

`ate/core/_check_data/live_usb_stamps.json`
`C:\Users\OoiJianHong\ate_preflight_out.txt`
