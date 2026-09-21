keywords: snippet-pointer, detect, wrap, list_detected_tests, located, trigger, UI_CONTRACT, check_ui_contract
main_idea: Tests page Detect panel now scans golden file:line pointers and triggers them (no imported_*.py scaffold); UI shows detected+located rows and src hints on Test program.

## Snippet-pointer operator UI (2026-09-15)

Parent adds RPC fields; this slice is UI-only (`index.html`, `app.js`, `UI_CONTRACT.md`, `check_ui_contract.py`).

### Law
- UI never rewrites test Python. Scan remembers `file:lineno`; Wrap/Remember triggers by id.
- Params/limits stay in `ate/tests/`, `ate/config/parts/`, `ate/config/limits/`.

### HTML (`#panel-detect-scan`)
- Title: **Scan / trigger snippets**
- Hint replaces scaffold copy with snippet-pointer language (must include `this Version` + `snippet`/`pointer` for contract check).
- Cache bump: `styles.css?v=20260915snip1`, `app.js?v=20260915snip1`

### JS (`app.js`)
- `refreshDetectedPanel`: merges `res.detected` + `res.located` into `detectedCache` (`matched: true|false`).
- `paintDetectedRows`: both row kinds; located = `(trigger · product)` + `already in registry`; unmatched ready = `trigger-ready`; blocked = disabled checkbox.
- Button: **Remember + enable on this Version**; alert: **Tick one or more trigger-ready rows**.
- `wrapSelectedDetected` log: `Trigger ${id} at file:line (mode)` from `res.snippet`.
- `loadTests`: optional `src path/line` from `t.source` (last 2 path segments).

### Contract / check
- `UI_CONTRACT.md` item 14: scan/trigger, no `imported_*` scaffold requirement.
- `check_ui_contract.py`: requires `this Version` AND (`pointer` OR `snippet`); drops `scaffold` requirement.

### Verify
```bat
venv\Scripts\python.exe -m ate.core.check_ui_contract
```
