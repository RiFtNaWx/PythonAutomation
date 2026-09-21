---
keywords: path-b, write-test, cursor-prompt, prompt-engineering, check_add_test, check_ui_contract, save_path_b_test, config, catalog
main_idea: Tests page now configs (catalog + params Write), adds (Save this Version / Remember), writes Path B files, and copies a filled Path A/B/C Cursor prompt. Checks refuse input() and reserved runner id.
---

PREFLIGHT: PARTIAL reuse `2026-09-15_own-code-bank-sim.md`, `2026-09-15_per-test-params.md`, `2026-09-15_snippet-pointer-ui.md`.

## Operator click path

1. Setup Apply campaign (person, not All).
2. Test program row: Parameters + Write (this Version `test_params.yaml`). Edit source opens Path B editor.
3. Tests tab Customize + Save this Version (Path A catalog).
4. Write test: Load template, Save Path B file (`ate/tests/<family>/<id>.py`). Idle-restart, DEMO that id.
5. Cursor prompt: pick Path A/B/C, Fill, Copy. Paste into Cursor.

## Checks

`python -m ate.core.check_add_test`
`python -m ate.core.check_ui_contract`

Does not edit `runner.py`.
