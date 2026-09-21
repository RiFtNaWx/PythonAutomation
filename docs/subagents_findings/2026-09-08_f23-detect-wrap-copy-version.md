---
keywords: f23, a16, detect, wrap, copy, version, session, golden, test_detect, input-block
main_idea: F23/A16 ships AST detect of unmatched def test_*, wrap clean ones into TestSpec, same-family enable/copy, Setup +Version/+Session. input() blocked. No Monaco. A03 closed; no-code wizard still parked.
---

# 2026-09-08 F23 detect / wrap / copy / +Version

## Shipped

- `ate/config/golden_roots.yaml` + `ate/core/test_detect.py`
- RPCs: `list_detected_tests`, `wrap_detected_test`, `enable_tests_on_part`, `ensure_version`, `new_run_session`
- Setup UI: + Version, + Session, Detected tests panel, copy-from-part
- `python -m ate.core.check_test_detect` (OK)
- `load_family` reloads package so runtime-added modules register

## Parked

- In-browser code editor
- RS1G07 CPD/CIN physics (dirty goldens with input() stay blocked)
- No-code wizard; A13/A14

## Check

```
python -m ate.core.check_test_detect
```
