---
keywords: new-product, demo, inventory, run-ic, ensure_product, run_demo, tracking-sheet, folders
main_idea: Enter a part we are testing to auto-create campaign folders; DEMO walks mock MSO/PSU/AWG/DMM and writes session JSON without stamping lab xlsx PASS. Do not scrape en.run-ic.com SKUs (RS724-Q1).
---

# New product folders + DEMO dry-run (2026-09-08)

## What shipped

- `ate/config/run_ic.yaml`: RUN-IC Product Center classes -> `#Test_Database` component + live family. Comparator / Interface / Vref / Power / Data conversion / Clock stay `live: false`.
- `ate/config/inventory.yaml`: tracking-sheet parts only (RS622, RS2323, RS0204, Logic Series, LDOs). **Not** homepage SKUs RS724-Q1 / RS722P-Q1 / RS721P-Q1 / RS8561.
- Setup **New product under test** -> RPC `ensure_product` creates Version_1 tree, stub yaml if missing, `os.startfile` the folder.
- **DEMO dry-run** -> RPC `run_demo`: mock instrument plan, `sessions/*.json`, `DUT_1/graphs/demo_sample.json`. START stays session-gated.
- Stub components (Power, Comparator, ...) must not `family_for_component` steal OpAmp.

## Operator flow

1. Pick tracking row or type part + RUN-IC class.
2. Create folders + open.
3. Live families: Apply campaign, tick tests, DEMO (no hardware) or Discover / Open Session / START.
4. Tweak freq / amp / repeats under Advanced bench.

## Checks

```
python -m ate.core.check_new_product
```

Does **not** prove hardware START or lab-report PASS.
