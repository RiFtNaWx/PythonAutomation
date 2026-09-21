keywords: analog-switch, switch-family, operator, lim, rs2323, rs2227, rs1g97, rs1g126, run-ic, f20
main_idea: Family rail is RUN-IC product class (Analog Switch, not a person). Lim is an operator who defaults AnalogSwitch/RS2323; his RS1G97/126/125 stay Logic. Do not import Downloads/code.

# F20 product class vs operator

## RUN-IC class (checked)

| Part | RUN-IC class | ATE family | Owner |
|------|--------------|------------|-------|
| RS2323 | Dual SPDT analog switch | switch | Lim |
| RS2227 | DPDT USB analog switch | switch | Lim |
| RS1G97 | Configurable logic gate | logic | Lim |
| RS1G126 / RS1G125 | 3-state bus buffer | logic | Lim |
| RS1G08 / RS1G32 / RS1GT32D | Small logic | logic | Ariff |
| RS1G07 / RS1G14 | Logic | logic | Eugene |
| RS29511 | Logic / level shifter | logic | Soo |
| RS0204 | Level translator | logic | ATE |
| RS622 / LM358 | OpAmp | opamp | Eugene |

Sources: run-ic.com analog-switch pages for RS2323/RS2227; logics pages/PDFs for RS1G125/RS1G97.

Reports folder: `Downloads\OneDrive_2026-09-03\Product Testing Report` (14 part folders).
Lim codes: `Downloads\code\RS1G97` and `RS1G126` only. Not imported (`input()` waits).

## What shipped

- Family key `switch` -> `ate.tests.lim` (package name historical). Alias `lim` -> `switch`. Rail label **Analog SW**.
- Campaign folder `#Test_Database\Lim` renamed to `AnalogSwitch`.
- Top-right Operator select from `ate/config/owners.yaml`. Picking a person jumps their default campaign; other families stay on the rail.
- Extra inventory campaigns (stub maps, no Lim wrap): RS2227, RS1G126, RS1G97, RS1G125, RS1G32, RS1GT32D, LM358.

## Checks

- `check_family_load`: `switch=4` (not lim=4); `load_family("lim")` aliases to switch
- `check_open_inventory` / `check_mapped_tests` / `check_logic_campaign` OK
- Worker **0.2.12**. Console Ctrl+F5 `?v=20260903p`

## Ceiling

- RS2227 reuses RS2323 current test ids until USB DPDT recipe exists.
- SOP8 under AnalogSwitch/RS2323 is leftover OpAmp-shaped folder; real campaign is MSOP.
- Do not wrap `Downloads\code`.
