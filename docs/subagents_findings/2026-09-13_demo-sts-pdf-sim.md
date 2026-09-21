---
keywords: [demo, sim, pyvisa, sts-pdf, limits, rs622, slew, psrr, version-folder, records]
main_idea: DEMO already uses the real START path on fake PyVISA. It was not smooth for OpAmp because SIM always returned 0.120 (slew Cnt=0, CHAN offset mismatch). Now SIM tracks AWG APPL/OUTP and scope SCALE/OFFS/MEASURE. Same Version folder, per-test records, complete Status + STS PDF.
---

# 2026-09-13 DEMO smoothness + STS PDF

## What DEMO already was

DEMO = `open_session({sim:true})` then the same `run_sequence` as START. Selected tests only. Fixture batches stay separate (BUFFER then ATE). Living `sessions/report.json` merges into this operator Version; it does not wipe tests you did not tick and does not clone Version. Per-test history is `{test}/DUT_n/records/*.json`.

The attached `RS662 time (1).pdf` is an STS8200 DC scan (OS_/IDD_/PSRR/CMRR/AOL), not a timing datasheet. Lab slots stay slew/GBW/ORT/mapped_dc. OS_/IDD_ limits were already in `ate/config/limits/rs622.yaml`. Do not invent a second STS8200 handler.

## What was broken

SIM MEASURE always returned 0.120, so slew `COUNt` never reached 80. Scope CHAN OFFS writes were ignored, so NEG slew failed readback. Mapped PSRR returned a screenshot with no datasheet stamp. Results only had a buried pass/fail hint; export errors were swallowed.

## Shipped

- SIM: AWG APPL bus, COUNT=120, VPP follows programmed amplitude, CHAN SCALE/OFFS readback, GBW CHAN2 roll-off near 7 MHz/11
- Slew stamps `SR_Vus`; empty SIM measurements (PSRR/CMRR/AOL) use datasheet typ vs min/max
- RS62X table 7.4: PSRR min 78 / CMRR min 74 / AOL min 96; IQ max 800
- Results `#results-sts-status` + Run banner `Complete: status · Total / Pass / Fail` + `sessions/datalog.pdf` (Status line like the STS sheet)
- `python -m ate.core.check_sim_run` now covers RS622 slew+psrr records + PDF

## Check

```
python -m ate.core.check_sim_run
python -m ate.core.check_specs_datalog
python -m ate.core.check_ui_contract
```

Does not prove live USB START, 4-DUT hardware, or production OS_/IDD_ openshort (those are STS8200, not lab TestSpecs).
