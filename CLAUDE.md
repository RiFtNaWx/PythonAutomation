# Claude / Cursor / Copilot -- read this first

This file is the **system prompt** for every AI agent on this repo. Do not ask the operator to paste a prompt. You already have it.

1. Read **[AGENTS.md](AGENTS.md)** before any edit. That is the map (where to change, Path A/B/C, blast radius).
2. Always-on skills (clone-installed): `.cursor/skills/ate-prompt/`, `ate-add-test`, `ate-ocr`, `ponytail`, `i-have-adhd`.
3. Always-on rule: `.cursor/rules/ate-skills-compulsory.mdc`.
4. How: [docs/VIBE_CODE.md](docs/VIBE_CODE.md). Datasheet ingest is local: `python -m ate.core.ingest_datasheet <PART> --pdf <file> --xlsx <file>`.

Live product is `ate/` + worker **8766** + UI **5174**. Do not invent a second stack. Do not scrape en.run-ic.com into `#Test_Database`. Do not guess Excel cells (probe the live xlsx). Do not call `input()` in `TestSpec.run`.
