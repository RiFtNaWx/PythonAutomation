---
keywords: [sts-datalog, min-max, pass-fail, en.run-ic, limits-yaml, prompt-guide]
main_idea: After each START/DEMO, measurements get datasheet min/typ/max and PASS/FAIL. Export STS datalog.md/.html/.pdf. English RUN-IC fetch fills ate/config/limits/<part>.yaml only, never #Test_Database.
---

# STS datalog + datasheet limits (2026-09-11)

Pass/fail uses min and max only. typ is display-only. Missing spec -> unspec, does not fail the step.

## Where it lives

- Limits: `ate/config/limits/<key>.yaml` (RS622 seeded from English RUN-IC + STS8200 sheet).
- Judge: `ate.core.specs.judge_value` / `record_step` stamps `result`.
- Export: `ate/reporting/sts_datalog.py` -> campaign `sessions/datalog.md|.html|.pdf`.
- Fetch: Results -> Fetch English datasheet limits. Host `en.run-ic.com` only. Merge does not clobber filled min/max. Keeps `test_info`.
- Prompts: `docs/PROMPT_GUIDE.md`.

## Do not

- Scrape en.run-ic.com SKUs into `#Test_Database`.
- Treat typ as a pass/fail window.
- yaml.safe_dump `parts/rs622.yaml` (comments).
