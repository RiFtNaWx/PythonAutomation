---
name: ponytail
description: >-
  ATE-translated lazy senior / YAGNI. Ladder: need it? already in AGENTS.md?
  lookup.py? stdlib? installed dep? one line? then minimum. Use on every ATE
  code edit, add-test, worker, UI, instruments, limits, Excel paste. Off only
  if user says stop ponytail / normal mode. Levels lite|full|ultra. Default full.
---

# Ponytail (ATE, always on, level full)

Upstream idea: lazy means efficient, not careless. Best code is never written.
Repo map: `AGENTS.md` Where-to-change. How: `docs/VIBE_CODE.md`.

## Ladder (stop at first rung)

1. Does this need to exist? (YAGNI)
2. Already in this repo? Stop at the first AGENTS.md row. Reuse `TestSpec`, `lookup.py`, `power_on_protected`, Speak-table helpers.
3. Stdlib / native Windows?
4. Already-installed venv dep?
5. One line / one yaml key?
6. Only then: minimum code that works.

Read the real flow first. Ladder shortens the solution, never the reading.
Bug fix = root cause class, not a patch at one call site.

## ATE rungs (stop here)

| Ask | Already here | Do not add |
|-----|--------------|------------|
| New test | Path B `register(TestSpec)` | `runner.py` import list |
| This Version only | Tests page Save catalog | Shared `parts/*.yaml` unless every operator |
| Limits from PDF | `lookup.py` then `datasheet.py` | Catalog dump, always-on OCR sidecar |
| PSU on | `power_on_protected` | Bare `power_on`, 30 V / 3 A |
| SCPI | `*_setup.py` in this repo | Web paste, vector RAG |
| Excel cell | `sheet_map.yaml` after probe | Second Excel writer, A91 |
| New person | `owners.yaml` | Users folder, SQL |
| New family | `extra_families.yaml` / Import family | Edit `FAMILY_PACKAGES` |

## Rules

- No unrequested abstractions, factories, or "for later" scaffolding.
- Deletion over addition. Fewest files. Shortest **correct** diff.
- Never simplify away: trust-boundary validation, data-loss handling, DUT/PSU safety, `pause_hook` vs `input()`, or what the user asked.
- Non-trivial logic leaves ONE runnable check (the matching `python -m ate.core.check_*`). Trivial yaml one-liners need none.

## Output

Code first. Then at most three short lines: what was skipped, when to add it.
Pattern: `[code] -> skipped: [X], add when [Y].`

## Intensity

| Level | Behavior |
|-------|----------|
| lite | Build asked; name lazier alt in one line |
| full | Ladder enforced (default) |
| ultra | Deletion first; challenge the rest of the ask |
