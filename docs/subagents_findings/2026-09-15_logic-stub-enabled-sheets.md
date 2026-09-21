---
keywords: junior, excel, provision, stub, cin, cpd, tp, ioff, clk_q, leftover-honest
main_idea: JianHong Parameter stubs now have one sheet per enabled logic lab_sheet (CIN/CPD/TP/Ioff/TW/Q7) with DUT F2:I2 paste. Existing stubs are never replaced by a golden copy2.
---

# Logic stub enabled sheets (CIN/CPD/TP)

Scan found 14 JianHong logic stubs missing CIN/CPD/IoffLeakage/TP/TW/Q7.

`_TEST_DUT_MIDS` now includes cin/cpd/ioff_leakage/tp/clk_q/pulse_width/serial_shift/delta_supply_current/input_leakage_sweep/ioz. Parameter DUT grids probe F2:I2 (CLKQ/TPD two-row).

`create_clean_golden_workbook` on an existing stub only syncs missing tabs. It does not `copy2` a golden over the Parameter book. New campaigns with no dest still copy the golden when one exists.

JianHong live: 29 campaigns, 0 missing enabled lab_sheets (golden Cin/tPD/VIX alias-match Parameter CIN/TP/VIH_VIL). RS2323 UQFN got Ron/Vth/TON/CinConCoff/TBBM Parameter tabs back on the copied leakage golden.

## Leftover-honest

- Analog-switch BW/ISO/XTalk. USB rON min/max PDF image.
- OpAmp AOL/EMIRR mapped. Settling photo, not 0.1% us. Noise is Vpp.
- RS0302 64 mA RON. No tPLH 1.2 ns body.
- Path C `input_off_leakage` unfilled, not enabled.
- USB START of every SKU is not SIM. Not junior-100%.

## Proof

```
python -m ate.core.check_campaign_outline
python -m ate.core.check_provision_operator
```

Live RS164 JianHong CIN_pF F2:I2, clk_q CLKQ_PHL_ns. RS2323 JianHong RON_ohm F2:I2.
