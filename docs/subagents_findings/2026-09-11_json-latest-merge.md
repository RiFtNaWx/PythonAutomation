---
keywords: a18, report.json, merge, latest, records, coverage, status-md, json-latest-merge
main_idea: Living sessions/report.json merges by test_id+dut(+channel) so a subset START keeps older tests; per-DUT records/ history; STATUS.md for boss Done/Ongoing/Not-complete.
---

# 2026-09-11 A18 JSON latest merge + STATUS

PREFLIGHT: PARTIAL. Reuse: 2026-09-08_a17-tags-session-datalog. Spawn: skip.

## Shipped

- `STATUS.md` (boss paste) + README Docs map row
- `ate/core/datalog.py`: load+merge `report.json`; `write_step_record` under `{test_key}/DUT_n/records/`
- `coverage` list on living report (`latest` | `missing`)
- `check_tags_datalog` asserts ort kept after gbw-only second START + both records files
- AGENTS.md rows for living JSON + records/

## Next (not this wave)

- A19 standard Excel + numeric auto-fill from JSON (all families)
- A20 complete limit P/F + sheet-quality PDF (limits yaml beyond RS622)
- Setup UX leftovers (auto-Apply on combo, dual operator pickers, tag duplication)
- R-0003 on A07-A12; stub RUN-IC classes stay empty


## Check

```
python -m ate.core.check_tags_datalog
```

OK this turn.
