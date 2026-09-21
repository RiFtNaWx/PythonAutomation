---
keywords: golden-gateway, tutorial, safety, ingest, push, syntax, blast-radius, leftover-honest
main_idea: People write goldens in original format; UPDATE_GOLDENS.bat imports when sources are newer; push.bat runs AST+mix gateway on the dirty tree only and does not rewrite author bodies.
---

## What landed

- Tutorial: `goldens/TUTORIAL.md` (write `*tests.py` + limits + `main.py`, import, gated push, debug table).
- Import: `UPDATE_GOLDENS.bat` -> `python -m ate.core.golden_gateway --import --verify` (copy only if source `.py` newer, unless `--force`). Never executes vendor modules. Never edits `ate/tests/` or `runner.py`.
- Safety: `verify_push` on **uncommitted** files only. Mixed `goldens/` + blast (`runner.py` / `database.py` / `registry.py` / worker / `ate/ui/web`) is blocked. SyntaxError prints `file:line` + fix that file only.
- Push: existing `push.bat` / `Github_Auto/git_helper.py` calls `verify_push(porcelain)` before Sea-Lion / commit. Gateway does not `git push` itself.
- Checks: `python -m ate.core.check_golden_gateway` plus TUTORIAL required by `check_ingest_goldens`.

## Leftover-honest

- Direct `git commit` bypasses the helper. Zip operators still do not push.
- Sea-Lion still only drafts the PR title; it is not a logic reviewer.
- `input()` goldens still run via that tree `main.py`; console Path C stays blocked until Path B `pause_hook`.
