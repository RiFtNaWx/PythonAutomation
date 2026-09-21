---
keywords: dut-count, sample-size, probe-channels, run-prefs, sts-pdf, customise, no-yaml
main_idea: DUT count (1-16) and Channel A/B are Setup ticks saved on this Version (run_prefs), not parts yaml. STS PDF prints whatever DUTs/channels/tests actually ran.
---

# Campaign DUT/channel customise (2026-09-14)

Operator asked not to edit yaml per SKU. Setup now has DUT count 1-16 plus A/B ticks. Values persist in `_manifest/run_prefs.yaml` (same file as walk order). Family default still seeds A vs A+B; ticking B on Logic is allowed and START runs it.

STS markdown/html/pdf add a Channel column and a header line of DUTs / channels / tests from the session steps, so adding DUT 8 or dropping a test does not need a 4xA+B template.

Runner no longer clips CHB from part yaml.

Skipped: growing Excel golden photo boxes past the live sheet geometry -- add when a campaign xlsx actually has extra DUT columns.
