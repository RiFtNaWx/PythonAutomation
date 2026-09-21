---
keywords: usb, buffer, slew, vpp, probe, psu-on, awg-ch1, tmo, hang, rs622
main_idea: Live bring-up DID turn DP832 CH1+CH2 2.5V ON and DG822 CH1 square 1kHz 1Vpp. MSO JPEG is flat ~18mV. Probes not on IN+/VOUT. Slew then wedged VISA; worker killed.
---

# 2026-09-14 BUFFER bring-up: PSU/AWG ON, MSO flat

PREFLIGHT: HIT 2026-09-14_usb-slew-tmo. Spawn: skip.

User: did not see devices ON; wants AWG CH1, MSO record, all BUFFER tests, logs/PDF.

## What is proven

- 09:03:24 DP832 CH1=ON 2.50V CH2=ON 2.50V Ilim=0.1A. DG822 CH1 OUT=1 APPL SQU 1kHz 1Vpp.
- MSO screenshot `SlewRate/DUT_1/screenshots/bringup_PSU_AWG1_2026-09-14_090326.jpg` Vpp1=18.3mV Vpp2=9.5mV. Flat traces.
- Log: `C:\Users\OoiJianHong\AppData\Local\Temp\ate_bringup.log`

## What failed

- Slew START after that hung on MSO USB (~7 min). `stop` RPC also hung (VISA not thread-safe). Worker killed. Power-off script then wedged on the same USB.
- Did not run SSSR/LSSR/NPR/POT: those stamp Excel PASS from a photo even if the trace is flat.
- Living `datalog.md` still shows old DEMO slew PASS. Not this USB run.

## Next

Front-panel DP832 OFF if still lit. Clip MSO CH1 to IN+ / AWG CH1, CH2 to VOUT. Unplug/replug MSO USB. Then START slew only.
