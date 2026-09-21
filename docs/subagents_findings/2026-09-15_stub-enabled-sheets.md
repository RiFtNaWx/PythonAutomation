---
keywords: junior, excel, provision, stub, usb_ron, i2c, rs0302, rs2227, paste-values, leftover-honest
main_idea: Parameter stubs now get one sheet per enabled TestSpec lab_sheet (not Setup-only). JianHong RS0302/RS2227/RS2323 UQFN stubs synced. USB TON/TOFF use named A-column rows.
---

# Enabled-test Parameter sheets on stubs

`create_clean_golden_workbook` used sheet_map tests only. Empty map -> Setup-only book -> Fill Excel had nowhere to put `usb_ron` / `i2c_ii`.

Now stubs take sheets from `enabled_tests` `lab_sheet`. Multi-id tests write A2/A3 measurement ids. `attach_known_values` probes those rows.

Live stubs updated (JianHong only; senior goldens skipped):

- RS0302: II / RON / Cioff
- RS2227: RON + TonToff (USB_TON_ns F2, USB_TOFF_ns F3)
- RS2323 UQFN: Ron / Vth / TON / CinConCoff / TBBM

## Leftover-honest

- USB rON min/max still PDF image. Analog BW/ISO/XTalk. AOL/EMIRR mapped. Settling photo not 0.1% us. RS0302 64 mA RON. USB START of every SKU is not SIM.

## Proof

```
python -m ate.core.check_campaign_outline
python -m ate.core.check_provision_operator
```
