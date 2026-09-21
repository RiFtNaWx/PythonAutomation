---
keywords: junior, excel, analog-switch, iplus, dut-grid, paste-values, leftover-honest, rs2227, rs2323
main_idea: Parameter DUT_1 headers map IPLUS/IOZ/ION/IIN to F2.. not Iplus B2 (Unit column). SeeLim stub stays B2. USB rON still has no Excel sheet.
---

# Analog-switch Parameter DUT paste

Live JianHong RS2227 / RS2323 UQFN books are Parameter grids (`DUT_1` on row 1). Old Iplus stub B2 is the Unit column there.

`attach_known_values` now probes DUT_n headers and stamps DUT-indexed cells. SeeLim MSOP stub with no DUT headers keeps `IPLUS_uA: B2`.

Applied campaign maps:

- AnalogSwitch/RS2227/MSOP/JianHong/Version_1
- AnalogSwitch/RS2323/UQFN1.4X1.8-10/JianHong/Version_1

## Leftover-honest

- USB `usb_ron` / `usb_ton_toff` have no RON sheet on the Parameter book.
- SeeLim MSOP LeakageOff/On/InputLeakage still have no DUT columns (stub).
- VOX yaml corners with no sheet row. RS0204 Icc/VOH grids. AOL/EMIRR mapped. Analog BW/ISO/XTalk.
- USB START of every SKU is not SIM.

## Proof

```
python -m ate.core.check_campaign_outline
python -m ate.core.check_session_values
```
