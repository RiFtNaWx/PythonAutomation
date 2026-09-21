---
keywords: own-code, allow-others, golden-bank, snippet-edit, logic_tests, INDEX, sim, fake-signal, leftover-honest
main_idea: Scan/Remember/Save stay on this person's goldens unless Allow other people's goldens is ticked. Open golden bank jumps to goldens/TUTORIAL.md. Save refreshes INDEX.md. SIM fake AWG/PSU already triggers every enabled TestSpec (213/213).
---

PREFLIGHT: HIT
reuse: `docs/subagents_findings/2026-09-15_snippet-pointer-working.md`, `2026-09-15_ingest-goldens-original.md`, `2026-09-15_person-name-canon.md`
spawn: skip

## Shipped

- Default scan author = this operator. Client `author=ariff` is ignored until `allow_others`.
- Wrap/Save of another person's golden raises until the tick.
- Tests page: `#detect-allow-others`, locked `#detect-author`, `#btn-open-golden-bank` -> `goldens/` GUIDE/INDEX/TUTORIAL.
- `save_snippet_source` rewrites `goldens/INDEX.md` after a golden `.py` save (syntax-checked, original file only).
- Soo files under `goldens/eugene/Soo/` author as soo, not eugene.

## Already here (not rebuilt)

- Path C pointer + trigger (`snippet_map.yaml`).
- SIM PyVISA bus (`ate/instruments/sim.py`) + `check_sim_run` + `check_all_parts.sim_run_all_enabled`.
- Catalog isolation (do not merge other people's `test_catalog.yaml`).

## Fake signal (makes sense)

- AWG SQU ON -> SIM DMM current scales with freq/Vpp (CIN/CPD).
- AWG OFF -> COUNT/Vpp drop.
- PSU OFF -> DMM ~0; PSU ON static ~0.8 uA.
- DC VIN sweeps stay flat in SIM (no USB leakage physics). USB later.

## Checks that ran

```
python -m ate.core.check_test_detect
python -m ate.core.check_ui_contract
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
python -m ate.core.check_ingest_goldens
python -m ate.core.check_stimulus
python -m ate.core.check_add_test
```

`check_all_parts` SIM 213/213 parts=26.

## Leftover-honest

- A16 `imported_input_off_leakage.py` stays.
- Copy-between-people catalogs stay parked. Allow-others is Path C trigger of their original file, not a catalog merge.
- Vendor `input()` / `Lim.*` still blocked for live wrap.
